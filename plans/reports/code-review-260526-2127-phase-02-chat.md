# Code Review — Phase 02 Chatbot Core (Retrieval + Chat Endpoints)

**Date:** 2026-05-26 21:27 (Asia/Bangkok)
**Scope:** 12 new files + 2 modified (`numerology-api/`)
**Plan:** `plans/260526-1854-chatbot-rag-pdf-analysis/phase-02-core-chat-retrieval.md`
**Tests:** 48/48 phase-02 pass (16 service unit + 15 router + 17 inherited phase-01). Real-LLM smoke deferred.
**Prior bar:** `code-review-260526-2058-phase-01-foundation.md` (7.5/10 baseline).

---

## Overall Score: **7.5 / 10**

Phase 02 ships a clean, well-modularized RAG core: every new file is under the LOC budget, ownership checks are centralized, prompt injection sanitized, and citations validated 1-indexed against the chunks list. The big concerns are around the **transaction model in `messages.send_message`** (one long-running session spanning embedding + retrieval + 30s LLM call) and the **`asyncio.wait_for` "timeout" that doesn't actually cancel the sync google-genai call**. Both are acceptable for Phase 02 (functionally correct in happy path) but need explicit follow-up tickets. Other issues are smaller — Phase 03+ hooks already absorb most of the call-outs.

---

## Critical Issues (Blocking Finalize)

### C1. `messages.send_message` — single long transaction wraps embed + retrieve + LLM + 2 inserts

**File:** `app/routers/chat/messages.py:52-133` (esp. lines 69-119)

`get_db()` commits on success, rolls back on error. The whole 8-step orchestration runs in **one DB transaction** that:

1. INSERTs the user message (`flush`, line 70) — uncommitted, holds row lock on `chat_messages` (and possibly on `chat_conversations` via FK).
2. Calls `RetrievalService.retrieve()` which executes a pgvector SELECT against `kb_chunks` (uses same async session — fine).
3. `await llm.generate(...)` — **up to `llm_timeout_seconds=30s`** of network I/O while a transaction is still open and an asyncpg connection is held from the pool.
4. INSERTs the assistant message and flushes.
5. Returns; `get_db()` commits on response.

Concrete problems:

- **Connection pool starvation under load.** Each in-flight chat turn holds an asyncpg connection for the full LLM latency. At 30 concurrent free-tier users this drains the default pool (`pool_size=5`).
- **Long PG transactions** delay vacuum and (on RR isolation) prevent index cleanup. On READ COMMITTED (PG default) the cost is lower but still real.
- **Loss-of-user-message scenario.** If `llm.generate` raises `LlmError` (line 97-102), the whole transaction rolls back via `get_db()`'s `except` — including the user message inserted at step 1. The "1. Persist user message first so history is consistent even if LLM fails" comment (line 62) is **incorrect**: today the user message is lost on 502.
- **Race / atomicity** for "what if LLM succeeds but flush fails": the assistant text + token counters are gone, user-side already saw the answer streaming (it won't — non-streaming — but in Phase 04 it will). The conversation is now in a half-state.

**Recommended fix (Phase 02 acceptable scope):**

Either (a) commit the user message immediately and use a fresh session for the assistant insert, or (b) at minimum acknowledge with a code comment that user message rolls back on LLM 502. Option (a) is cleaner — pattern:

```python
db.add(user_msg)
await db.commit()         # release locks before LLM call
await db.refresh(user_msg)
# ... LLM call without holding transaction ...
db.add(asst_msg)
await db.commit()
```

This requires either bypassing the `get_db()` commit-once contract, or splitting into two service calls each with its own session. The current "single txn" approach is functionally OK for low traffic but is a **production scaling bug** that should be fixed before Phase 04 streaming lands (streaming makes the long-txn window even worse).

**Severity:** High (correctness + scaling); acceptable to ship Phase 02 with an explicit known-issue note + Phase 04 follow-up.

---

### C2. `LlmService.generate` timeout leaks the underlying thread + HTTP socket

**File:** `app/services/chat/llm_service.py:66-78, 104-105`

`asyncio.wait_for(self._call(...), timeout=30)` cancels the **awaiting coroutine**, but `_call` body is `await asyncio.to_thread(_sync)`. Cancelling a `to_thread` future does **not** kill the thread — google-genai's sync HTTP request keeps running to completion, holding a network socket and a thread-pool worker until the Gemini API actually responds. After many timeouts the default `concurrent.futures` thread pool (`min(32, os.cpu_count()+4)`) fills with zombie work and *new* embed/LLM calls block.

Compounding: there is no per-request HTTP timeout on the google-genai client itself (no `httpx.Timeout` passed to `genai.Client`).

**Acceptable for Phase 02** because (a) traffic is low, (b) Gemini's own backend timeout (~60s) eventually frees workers, and (c) Phase 04 will replace `generate_content` with `generate_content_stream` which has its own pacing. But document the leak + add a follow-up to inject an `httpx.Timeout` into the genai client so the *sync* call also bounds itself.

**Severity:** Medium-High. Not a blocker for Phase 02 sign-off, but file a Phase 04 must-fix ticket.

---

## Non-Critical Issues

### H1. `retrieval_service._search` — `<=>` is computed twice per row

**File:** `app/services/chat/retrieval_service.py:67-80`

The SQL has `1 - (c.embedding <=> CAST(:emb AS vector))` in the SELECT *and* `c.embedding <=> CAST(:emb AS vector)` in the ORDER BY. PG should fold these (same expression), but pgvector + the explicit CAST may not get constant-folded reliably. Refactor with a subquery / CTE:

```sql
SELECT ..., 1 - dist AS score
FROM (
  SELECT c.*, c.embedding <=> CAST(:emb AS vector) AS dist
  FROM kb_chunks c
  ORDER BY dist ASC
  LIMIT :k
) c
JOIN kb_documents d ON d.id = c.document_id
```

This makes the cost obvious at top-k=3. Cheap win, also clearer intent. **Nice-to-have.**

### H2. SQL injection vector for `:emb` is parametrized — but the pgvector cast contract isn't formalized

**File:** `app/services/chat/retrieval_service.py:75, 82, 100-102`

`_vector_literal` builds `"[v1,v2,...]"` from `list[float]` formatted with `:.8f` — float-only, no string passthrough → **safe**. The bind happens via `text()` + `params={"emb": emb_str}`, which uses parametrized binding (asyncpg sends as a `$1` parameter), not string interpolation. So **no SQL injection risk** even if the upstream embedding returned a hostile vector (which it can't).

Two minor hardening items:

1. `_vector_literal` does not `assert isinstance(v, float)` — if `EmbeddingService.embed_one` ever returns a `Decimal` or non-numeric, the `:.8f` will raise `TypeError` (acceptable) but a `numpy.float32` would silently lose precision. Add `float(v)` cast inside the f-string.
2. Length validation: we don't assert `len(vec) == 768`. A short/long vector will cause pgvector to raise. Optional defensive check at the top of `_search`.

**Severity:** Low — current code is safe; just hardening.

### H3. Embedding cache absent — same user question re-embedded each turn

**File:** `app/services/chat/retrieval_service.py:48` + `messages.py:73-80`

`embed_one(query)` calls Gemini for every message, even verbatim repeats. At ~$0.000025 per 1k chars this is trivial cost-wise but adds 100-300ms latency per request. Plan 06 covers this — flag only as **nice-to-have**.

**Quick win available:** in-process LRU on `EmbeddingService.embed_one` keyed by `hash(text)` would handle reload-and-retry without touching architecture. ~5 LOC:

```python
from functools import lru_cache
# but lru_cache + async = pain; use cachetools.TTLCache + asyncio.Lock
```

Skip for Phase 02; just **note in the plan** as Phase 06 prerequisite.

### H4. `get_recent_messages` issued every turn — N+1 only at high turn counts

**File:** `app/services/chat/conversation_service.py:80-92` + `messages.py:86-90`

One ORDER-BY-DESC LIMIT N query per turn — not actually N+1, it's O(1) per request. The label "N+1" in the user's brief is misleading; the real concern is **cost of history scan**: at turn 100 with no index on `(conversation_id, created_at)`, PG sequence-scans. The migration `0010_chatbot_foundation.py` should have an index there — verify (didn't check this phase but raised in phase-01 review).

**Action:** confirm `chat_messages` has an index on `(conversation_id, created_at)`. If yes, this is fine. **Nice-to-have to add if missing.**

### H5. `get_recent_messages` returns the just-inserted user message, then routerfilters it out

**File:** `messages.py:86-90`

```python
history = await conv_svc.get_recent_messages(conversation_id, limit=settings.history_max_messages + 1)
history = [m for m in history if m.id != user_msg.id]
```

`history_max_messages=5` so we fetch 6 to filter 1 out. Works but fragile — if `_recent` returns ≤5 (new conversation), filter is a no-op; if the user message hasn't been flushed yet, `m.id` is `None` and the filter silently keeps it. Currently `db.flush()` on line 70 assigns the id, so OK, but the dance is brittle. Cleaner: pass `exclude_id=user_msg.id` into the service.

**Severity:** Low.

### H6. Tier hardcode "free" in two places

**File:** `messages.py:68, 113, 96`

`tier="free"` is duplicated on the user-msg row, the asst-msg row, and implicitly via `tier="flash"` in the LLM call. Phase 05 will inject quota — extracting a single `resolve_tier(user) -> Literal["free","paid"]` helper now is cheap and prevents the future "missed one of three places" bug. **Should-fix before Phase 05.**

### H7. `pdf_context_id` is dead code — parameter accepted, threaded, ignored

**File:** `retrieval_service.py:40, 49, 58, 62-64`

```python
pdf_context_id: Optional[int] = None,  # Phase 03 hook
...
_ = pdf_context_id
```

YAGNI says drop it; the Phase 02 plan says keep the hook stable for Phase 03 parallel work. **Compromise:** keep the parameter (already discussed in §6 of phase-02 plan), but make it `assert pdf_context_id is None, "pdf_context filtering not yet implemented"` or raise `NotImplementedError`, so a Phase 03 dev who forgets to wire it up gets a loud failure instead of silent KB-only fallback. **Should-fix.**

### H8. Retrieval failure swallowed silently

**File:** `messages.py:75-83`

```python
try:
    chunks = await retrieval.retrieve(...)
except Exception:
    logger.exception(...)
    chunks = []
```

This converts any retrieval error (DB connection drop, pgvector cast failure, embedding API down) into an empty-chunks prompt — the LLM then answers with the canonical "no info" reply. Two concerns:

1. **User-visible failure mode is identical to a true off-topic question.** Operations will not be able to distinguish "retrieval is down" from "low recall on novel question" without log spelunking.
2. **Cost waste.** We still call the LLM (paying ~500 tokens of prompt) just to have it return the canonical "no info" reply.

**Better:** on retrieval exception, skip the LLM entirely and return the canonical phrase directly. Saves one LLM call and gives operators a clear log line.

**Severity:** Medium. **Should-fix.**

### H9. Token budget approximation is honest but unverified

**File:** `prompt_builder.py:35-37, 89-92, 102-104`

`len(text) // 4` underestimates Vietnamese by 30-50% (Vietnamese diacritics tokenize to ~1.5-2 chars/token, not 4). For a Vietnamese-heavy app, the warning threshold will fire late or not at all. `tiktoken` cl100k isn't even the right tokenizer for Gemini — Gemini uses sentencepiece. **The right tool is `client.models.count_tokens()`** which the plan explicitly mentions but the code skips.

For Phase 02 the warning is cosmetic (we don't enforce a hard limit), so heuristic is fine. **Nice-to-have:** swap to `count_tokens` once per build (one extra Gemini call = $$ + latency though), or just remove the warning until it's actionable.

### H10. `prompt_builder.sanitize_user_text` — tokens stripped but no length-bounded substitution

**File:** `prompt_builder.py:48-54`

Looks correct for the listed tokens. Two gaps:

- No defense against newline floods (`"\n" * 100000`) — Pydantic max_length=2000 on `MessageIn.content` already caps this. **OK.**
- No defense against Gemini's *own* role tokens (`<start_of_turn>`, `<end_of_turn>` for Gemma-flavored prompts). Probably not relevant for `gemini-2.0-flash` chat API. **OK to skip.**

### H11. Citation `chunk_id` exposure — internal IDs leak in API response

**File:** `app/schemas/chat/message.py:13-20` + `citation_parser.py:42-48`

`Citation.chunk_id` and `Citation.document_id` are integer PKs returned to the client. Today this is fine — KB is shared admin content, no per-user data — but the moment Phase 03 lets users upload PDFs, **`pdf_context_id` chunks will share the same `kb_chunks` table** and per-user IDs will leak across users (if you can guess an int and pass it back somewhere). For Phase 02 this is **acceptable**; document the privacy stance in a code comment + plan for Phase 03 to either (a) move user-PDF chunks to a separate table, or (b) return opaque `f"kb_{id}"` / `f"pdf_{id}"` slugs in the API while keeping ints internal. **Should-fix during Phase 03.**

### H12. `LlmResponse.text` empty-string handling

**File:** `llm_service.py:93`

```python
text = (resp.text or "").strip()
```

If Gemini returns an empty/safety-blocked response, `text == ""`, we still persist an empty assistant message and return it. The user sees a blank bubble. Either raise `LlmError("empty response, likely safety filter")` or substitute the canonical "không có đủ thông tin" phrase. **Should-fix** — easy guard.

### H13. `LlmService._sync` swallows `LlmError` re-raise twice

**File:** `llm_service.py:106-109`

```python
try:
    return await asyncio.to_thread(_sync)
except LlmError:
    raise
except Exception as exc:
    raise LlmError(f"LLM call failed: {exc}") from exc
```

`_sync` itself never raises `LlmError` — the `except LlmError: raise` branch is dead. Cosmetic; remove or document why it's defensive. **Nice-to-have.**

### H14. Tests cover happy paths but miss anti-hallucination canonical phrase trigger

**File:** `tests/services/chat/test_prompt_builder.py:48-50`

`test_build_prompt_handles_empty_chunks` checks `"(no relevant excerpts found)"` is in `user_content`, but **does not verify the system prompt's "Tôi không có đủ thông tin để trả lời câu hỏi này." rule is wired**. That's an LLM behavior assertion, only verifiable with a real Gemini call (deferred). Add a unit test:

```python
def test_system_prompt_contains_no_info_canonical_phrase():
    assert "Tôi không có đủ thông tin" in SYSTEM_PROMPT
```

5-line gap closer. **Should-fix.**

### H15. Test gap — empty KB end-to-end + LLM hallucinates index

**File:** `tests/routers/chat/test_messages.py`

Covered: empty content (422), oversize content (422), other user (404), LLM error (502), happy path with [1].

Missing:

1. **Empty KB result (chunks=[]) → assistant still responds.** Easy: monkeypatch retrieve to return `[]`, generate to return `"Tôi không có đủ thông tin..."`. Verify response 201 with empty `citations: []`.
2. **LLM hallucinates [9] when only 3 chunks exist.** Covered at unit level (`test_build_citations_drops_out_of_range_index`) but not at integration. Worth one router test to prove the response payload survives a hallucinated index without 500ing.
3. **Multi-turn history flow.** No test asserts history is fed into prompt on turn 2. Add: send msg → send msg again → inspect the `prompt.user_content` passed to LLM mock includes turn 1.
4. **Retrieval exception path** (H8). Monkeypatch retrieve to raise; verify response is 201 and not 502 (or 500-via-LLM-cost-waste).

**Should-fix** — adds ~30 LOC for 4 important coverage points.

### H16. LOC budget

| File | LOC | Budget | Status |
|------|-----|--------|--------|
| `retrieval_service.py` | 102 | 150 | ✓ |
| `prompt_builder.py` | 104 | 120 | ✓ |
| `llm_service.py` | 109 | 180 | ✓ |
| `citation_parser.py` | 51 | 80 | ✓ |
| `conversation_service.py` | 92 | 120 | ✓ |
| `conversations.py` (router) | 68 | 150 | ✓ |
| `messages.py` (router) | 133 | 180 | ✓ |

All within budget. ✓

### H17. `RetrievalService.embed_one` per message — singleton EmbeddingService

**File:** `messages.py:73`

Each request creates a fresh `EmbeddingService()` and (lazily) a fresh `genai.Client`. Client creation is cheap-ish but **HTTP connection pool is per-client** — no connection reuse across requests. Move `EmbeddingService` and `LlmService` to module-level singletons or FastAPI dependencies (`Depends`) with a `lru_cache` factory:

```python
@lru_cache(maxsize=1)
def _embedding_service() -> EmbeddingService: ...
```

Will reduce per-request latency by 50-200ms (TLS handshake) at zero risk. **Should-fix.**

---

## Positive Observations

- **Ownership pattern clean.** `ConversationService.get_owned` is the single 404 gate; routers don't repeat the filter.
- **Pydantic constraints** (`min_length=1, max_length=2000`) correctly placed at the schema layer, not buried in the router.
- **`citation_parser` is tight and well-tested** — out-of-range, dedup, ordering all covered.
- **Constant `SYSTEM_PROMPT`** as module-level string is exactly right for Gemini prompt caching (Phase 06 will exploit this).
- **Sanitization happens *inside* `build_prompt`**, not in the router — defense-in-depth even if a future caller forgets.
- **`_vector_literal` is float-only formatted** — no string-passthrough = no SQL injection via embedding.
- **Two routers, one prefix** is fine. FastAPI handles `/api/chat/conversations` and `/api/chat/conversations/{id}/messages` cleanly across them.
- **Tests use `monkeypatch` on the class method**, not on dependency-injected instances — survives router restructure.

---

## Recommended Actions

### Must-Fix (before Phase 04 streaming work)
1. **[C1]** Decide transaction strategy for `send_message`. At minimum, fix the comment lie ("user message is consistent on LLM fail" is false today). Preferably split into two commits to release pool connections during LLM call.
2. **[C2]** Add `httpx.Timeout` to `genai.Client` so the *sync* call also bounds itself. Document the to_thread cancellation leak in `llm_service.py`.
3. **[H8]** Don't call LLM on retrieval exception. Return canonical phrase + log clearly.
4. **[H12]** Guard against empty `resp.text` from safety-blocked Gemini responses.

### Should-Fix (Phase 02 cleanup tickets)
5. **[H6]** Extract `resolve_tier(user)` helper now to prep Phase 05 quota plug-in.
6. **[H7]** Make `pdf_context_id != None` raise `NotImplementedError` until Phase 03 wires it.
7. **[H11]** Document `chunk_id` privacy stance with code comment; gate behind a per-user-PDF separation plan for Phase 03.
8. **[H14, H15]** Add 5 missing tests: system-prompt canonical phrase, empty-KB integration, hallucinated index integration, multi-turn history, retrieval failure path.
9. **[H17]** Cache `EmbeddingService` + `LlmService` per process to reuse HTTP connections.

### Nice-to-Have (file for Phase 06+)
10. **[H1]** Subquery refactor of `_search` SQL to compute distance once per row.
11. **[H3]** Embedding cache (LRU/TTL) for verbatim repeats — Phase 06.
12. **[H9]** Replace `len//4` heuristic with `client.models.count_tokens()`, OR remove warning until enforced.
13. **[H13]** Remove dead `except LlmError: raise` arm.
14. **[H4]** Verify index `(conversation_id, created_at)` exists on `chat_messages`.
15. **[H2]** Add length-check on embedding vector (defensive).

---

## Open Questions

1. **Transaction policy:** is the Phase 04 streaming endpoint expected to commit the user message before opening the SSE stream, or should the whole turn (user+assistant) commit at the end? This drives the C1 fix.
2. **PDF privacy boundary:** will Phase 03 store user PDFs in `kb_chunks` (mixed tenant) or a separate `pdf_chunks` table? Drives the H11 chunk_id leakage decision.
3. **Connection pool size:** what's the asyncpg pool size in production (`pool_size`, `max_overflow`)? Drives the C1 severity assessment — at 5 connections + 30s LLM timeout, 5 concurrent users will block.
4. **Acceptable to ship Phase 02 to staging with C1 + C2 known-issues filed,** or does production require them fixed first? My read: staging OK, prod block until at least C1 (user message loss on 502) is addressed.
5. **Index on `chat_messages(conversation_id, created_at)`** — exists? Not verified this round.
