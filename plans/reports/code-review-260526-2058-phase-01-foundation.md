# Code Review — Phase 01 Chatbot RAG Foundation

**Date:** 2026-05-26 20:58 (Asia/Bangkok)
**Scope:** 17 new files + 5 modified (`numerology-api/`)
**Plan:** `plans/260526-1854-chatbot-rag-pdf-analysis/phase-01-foundation-db-embedding.md`
**Tests:** 17/17 chat unit pass; full suite 193 pass / 14 pre-existing fails (unrelated).

---

## Overall Score: **7.5 / 10**

Solid, well-modularized foundation. All files within LOC budget. Idiomatic SQLAlchemy 2.0. Tests are sane (deterministic embeddings, retry/exhaust/non-retryable paths covered). A handful of correctness concerns and one **critical race condition** in `kb_sync.py` block a clean "ship to prod" stamp — none block code-complete sign-off for Phase 01 since prod runtime is deferred.

---

## Critical Issues (Blocking Finalize)

### C1. `kb_sync.py` — `asyncio.create_task` from sync event-listener thread

**File:** `app/services/chat/kb_sync.py:91-102`

SQLAlchemy `after_insert/update/delete` hooks fire on the SQLAlchemy thread that flushes the session. With async engine + asyncpg, this is the asyncio thread — so today this happens to work. But:

1. `register_kb_sync_listeners()` calls `asyncio.create_task(_worker())` at lifespan start. If a numerology CRUD fires *before* the lifespan task is alive, `_enqueue` silently drops events (`_queue is None` branch line 46-47) with **no log**. Confirm test path / dev startup never inserts content before listener registration completes.
2. `_enqueue` (line 45-53) calls `_queue.put_nowait`. Synchronous, fine. **But** the listener fires *inside* the SQLAlchemy `after_insert` hook — at this point the row's DB INSERT has executed but the outer transaction may not have committed yet. If the outer transaction rolls back, the queued upsert will reference a row that never existed. Worse, the embedding job may run before the commit — re-fetching content from DB inside `_process_one` won't find it. Today the queued payload is *self-contained* (title/content baked in at enqueue time), which masks the issue, but a stale-write race exists: rapid `update + rollback` enqueues a phantom doc.

   **Fix:** prefer `after_commit` session-level event over per-row mapper events, OR add a guard that fetches the row inside `_process_one` and skips if missing.
3. Module-level singletons `_queue` / `_worker_task` are not thread-safe and won't survive uvicorn `--reload` cleanly. Worker task is never awaited on shutdown — pending items in queue lost. **Add** `_worker_task.cancel()` + queue drain in lifespan's `finally` block.

### C2. `embedding_service._is_retryable` substring match is too permissive

**File:** `app/services/chat/embedding_service.py:114-117` + retry list line 22-33

`_RETRYABLE_SUBSTRINGS` includes `"internal"`. Any exception containing the word "internal" anywhere in `str(exc)` is retried — e.g. `ValueError("internal validation failed: bad model name")` from a typo would retry 3× wastefully. Similarly `"rate"` matches `"rate of change"` in hypothetical user-content errors.

Status codes `"500"`, `"502"` etc match as substrings — `Exception("got 500-character response")` would retry.

**Fix:** match on `google.api_core.exceptions` typed exceptions (`ServiceUnavailable`, `DeadlineExceeded`, `InternalServerError`, `ResourceExhausted`) — google-genai surfaces these. Substring fallback OK as last resort but should require word boundary `\b500\b`.

### C3. `kb_chunks.metadata` JSONB vs `kb_documents.metadata` JSON inconsistency

**File:** `alembic/versions/0010_chatbot_foundation.py:39, 69, 129`

- `kb_documents.metadata` → `sa.JSON` (renders as `JSON` on PG, not `JSONB`)
- `kb_chunks.metadata` → raw SQL `JSONB NOT NULL DEFAULT '{}'`
- `chat_messages.citations` → `sa.JSON`

PG `JSON` (not JSONB) stores raw text and re-parses on read — slower and no GIN indexing possible. For consistency + future indexability, use `postgresql.JSONB` on **all three**. ORM models in `kb_document.py:25`, `message.py:33` also need updating to `JSONB` (or import via `postgresql.JSONB`).

---

## Non-Critical Issues

### H1. `kb_ingestion_service._replace_chunks` atomicity comment is misleading

**File:** `app/services/chat/kb_ingestion_service.py:103-131`

Docstring says "Atomic" but the method only `await session.flush()` — it does **not** commit. Atomicity depends on the **caller** wrapping the call in a transaction and not commiting between flushes. In `kb_sync._process_one` (line 64-76) the commit *is* at the end, so OK. In `backfill_kb.main` (line 60-67) the commit is per-model loop — also OK. But if a future caller forgets to commit and the session is garbage-collected, chunks vanish. Rewrite docstring to "Atomic within caller transaction" + consider `async with session.begin_nested()` SAVEPOINT for true atomicity inside an outer txn.

### H2. `_replace_chunks` does embedding BEFORE delete — but flush order issue

**File:** `kb_ingestion_service.py:113-131`

Current order: embed → delete old chunks → insert new chunks → flush.

If embedding succeeds and DB INSERT fails (e.g. vector dim mismatch on a corrupt embedding), the existing chunks are now deleted and we've paid the embedding cost twice on retry. Two fixes either:
- Use a SAVEPOINT (`begin_nested`) so delete+insert is atomic
- Insert-then-delete-old by chunk_index offset (more complex)

For Phase 01 KISS — keep current behavior, add a comment + test for the failure mode.

### H3. `delete_document` doesn't fail-soft on FK CASCADE inconsistency

**File:** `kb_ingestion_service.py:57-64`

Relies on PG FK `ON DELETE CASCADE` to remove chunks. On SQLite tests with no real FK enforcement (default), orphan chunks could linger. Test `test_delete_document_removes_doc_and_chunks` only asserts no doc remains, not no chunks remain. **Add assertion** for chunks deleted, OR explicit chunk delete before doc delete (defensive).

### H4. Backfill script reuses underscore-prefixed `_to_source` import

**File:** `scripts/backfill_kb.py:20`

`from app.services.chat.kb_sync import _to_source` imports a private symbol. DRY but breaks encapsulation. Promote `_to_source` to public `to_source` (or move to a new `kb_sources.py` helper module) so both `kb_sync.py` and `backfill_kb.py` share it cleanly.

### H5. `PhoneMasterDataModel` filter duplicated

**File:** `app/main.py:96`, `scripts/backfill_kb.py:24`

Both filter `name != "PhoneMasterDataModel"` inline. DRY violation — extract `KB_INGESTABLE_MODELS` constant to `app/services/chat/kb_sync.py` (or new `kb_sources.py`).

### H6. `register_kb_sync_listeners` not idempotent

**File:** `kb_sync.py:91-102`

`event.listen(...)` is called every time. On a uvicorn `--reload` cycle the listener attaches a **second** copy → each CRUD enqueues 2× tasks. Use `event.contains(model, ..., _on_save)` check or store registered models in a module set.

### H7. Embedding payload size unguarded

**File:** `embedding_service.py:73-81`

`batch_size=100` is texts/request but Gemini also has a per-request byte limit (~36KB). A batch of 100 × 500-token chunks (~2000 chars each) ≈ 200KB → likely 4xx. Add total-bytes guard or lower default to 25.

### H8. `Chunker._apply_overlap` may exceed `max_tokens` per chunk

**File:** `chunker.py:101-109`

Prepends `overlap_tokens` to each window after packing. Window of 500 + overlap of 50 = 550 tokens. Embedding model accepts up to 2048 tokens for `text-embedding-004` so OK in practice — but `kb_chunks.token_count` will record 550 not 500. Test `test_overlap_present_between_chunks` allows tolerance; document in `Chunker` docstring that `token_count` includes overlap.

### H9. `KbChunk.metadata` ORM attr renamed but not used

**File:** `kb_chunk.py:30-32`

`chunk_metadata` (ORM) → column `"metadata"` (DB). `kb_ingestion_service._replace_chunks` (line 120-129) never sets `chunk_metadata`. Either drop the column for Phase 01 (YAGNI) or write metadata on chunk insert.

### H10. `chat_messages.created_at` missing `nullable=False`

**File:** `app/db/models/chat/message.py:34-37` + migration `0010_chatbot_foundation.py:130`

ORM has no explicit `nullable=False` (defaults to nullable=True on `datetime` without `Optional`). Migration also lacks NOT NULL. Compare with `TimestampMixin` style. Plan SQL spec line 112 has `NOT NULL DEFAULT NOW()`. Add `nullable=False` to both.

### H11. `chat_conversations.user_id` index not in migration

**File:** `0010_chatbot_foundation.py:85-109`

ORM declares `index=True` on `user_id` (conversation.py:25), but migration only creates composite `(user_id, created_at DESC)` index. SQLAlchemy autogenerate would diff this and emit a single-col index. Either remove `index=True` from the ORM (composite covers the prefix) or add the single-col index to migration. Recommend: drop `index=True` (composite suffices for both lookups).

### H12. `ChatMessage` SQL spec mentions DEFAULT '[]' for citations but `server_default="[]"` on JSON column

**File:** `message.py:33`, `0010_chatbot_foundation.py:129`

PG accepts `'[]'::json` literal; SQLAlchemy passes as string. Works but better explicit: `server_default=sa.text("'[]'::jsonb")` once switched to JSONB.

### H13. `_process_one` creates new `EmbeddingService()` per job

**File:** `kb_sync.py:67`

Constructs `EmbeddingService()` each call. Constructor is cheap (defers client creation) but each job builds a fresh `genai.Client` on first use — wastes HTTPS connection pool. Hoist a module-level singleton or pass through worker.

### H14. `EmbeddingService.embed_batch` empty-list returns before retry logic

**File:** `embedding_service.py:75-81`

Fine, but `_embed_with_retry(window)` with empty `window` would fire a wasted API call. Current loop slicing avoids this; just note the invariant explicitly.

### H15. `embedding_service` logs full exception message on retry

**File:** `embedding_service.py:95-98`

`logger.warning("embed retry %d/%d after error: %s ...", exc, ...)` — exception strings from google-genai may include the request URL **but not** the API key. Verified safe (google-genai 0.3+ uses headers). Document this assumption in the security comment.

### H16. SQLite vector storage works but `embed_batch` returns Python `list[float]`; pgvector bind processor handles serialization

**File:** verified at runtime by passing tests. No bug — pgvector's SQLAlchemy `Vector` type uses a `bind_processor` that converts list→string (`"[0.0,0.0,...]"`) regardless of dialect. SQLite stores as TEXT. **Cosine similarity queries cannot be exercised** on SQLite — covered by deferred PG integration test in Phase 02.

---

## Low Priority

- **L1.** `kb_sync.py:79-88` worker has no rate-limit / max-concurrency. A burst of 100 CRUDs queues 100 sequential embedding jobs (slow but safe). Acceptable for v1.
- **L2.** `0010_chatbot_foundation.py:167` comment says "Leave vector extension in place" — agree, but downgrade is now non-symmetric. Add a comment explaining the design choice.
- **L3.** `chunker.py:23-24` `_PARA_SPLIT` / `_SENT_SPLIT` regexes don't handle ellipsis / abbreviations ("Mr. Smith"). Acceptable for numerology content (mostly paragraph-form Vietnamese).
- **L4.** `embedding_service.py:43-49` `max_retries: int = 3` not pulled from settings — minor inconsistency with batch/model.
- **L5.** `pyproject.toml:27-29` versions are lower-bound only; pin upper bounds in production lockfile.
- **L6.** `kb_sync._reset_for_tests` (line 105-110) declared but no test actually calls it. Either use it in tests or drop.

---

## Security Review

| Concern | Status |
|---|---|
| `GEMINI_API_KEY` only via env, not logged | OK (`.env.example` placeholder, `config.py:80`) |
| API key in exception messages | OK (google-genai 0.3+ keeps key in header) — confirm w/ H15 |
| PII in KB content | OK (numerology generic text only) |
| Race condition on partial commit | See C1 (orphaned enqueue on rollback) |
| Vector blob inflation DoS | No size limit on `content` text before chunking. 100MB Vietnamese paragraph → 200k chunks → API spam. Add `max_input_chars` guard in ingestion. |
| SQL injection in `op.execute` raw blocks | Safe — no user input in migration strings |
| FK constraints | OK (CASCADE on conversation→message, document→chunk; SET NULL on created_by) |

---

## Positive Observations

- Excellent separation: chunker / embedder / ingestion are independently testable.
- All new files ≤200 LOC (max: ingestion 119, embedding 104).
- Cook report's fix for `Chunker.__init__ or → is None` is exactly right — captures a subtle bug.
- Test for non-retryable error path (`test_non_retryable_error_raises_immediately`) is the kind of negative test often skipped.
- Lifespan gate (`if settings.gemini_api_key`) is the correct pattern for dev/CI boot.
- `TimestampMixin` reused on `KbDocument` and `ChatConversation` — DRY.
- pgvector raw-SQL fallback for HNSW is the right call (SQLAlchemy DDL doesn't express HNSW opts cleanly).
- Deterministic fake-embedding fixture is cleaner than mocking the client per test.

---

## Recommended Actions

**Before Phase 02 starts (must-fix):**
1. Fix C1.2 — switch to `after_commit` session event OR add post-fetch validation in `_process_one` to skip non-existent rows.
2. Fix C2 — replace substring retry with typed exception check.
3. Add idempotency guard to `register_kb_sync_listeners` (H6).
4. Add lifespan-shutdown worker cancel + queue drain (C1.3).
5. Switch `metadata` JSON → JSONB on all 3 tables (C3).

**Should-fix during Phase 02:**
6. Promote `_to_source` → `to_source` + extract `KB_INGESTABLE_MODELS` constant (H4, H5).
7. Tighten `message.created_at` nullable=False (H10).
8. Drop or use `KbChunk.chunk_metadata` (H9).
9. Hoist `EmbeddingService` to module singleton (H13).
10. Add `max_input_chars` ingestion guard (Security).

**Nice-to-have:**
11. SAVEPOINT wrap in `_replace_chunks` (H2).
12. Integration test for cosine similarity against real PG (deferred per plan).

---

## Open Questions

1. **C1 disposition** — is the rare phantom-doc race (after_insert + outer rollback) acceptable to ship for Phase 01 given the workload is admin-only writes to numerology tables? If yes, document risk; if no, switch to `after_commit`.
2. **MainNumber multi-content** — same as cook report Q2: confirm one merged doc vs five separate docs (one per Roman numeral period). Affects chunk count + citation granularity in Phase 02.
3. **JSONB switch** — confirm we can break ORM column-type compatibility now (no production data exists yet on these tables). If yes, do it before backfill; if no, defer to Phase 04.
4. **Max input size policy** — what's the upper bound for a single document's content? Numerology rows are ~2KB but user-uploaded PDFs (Phase 03) could be 50MB+.
5. **Listener registration on bulk import** — `register_kb_sync_listeners` will fire on every row during `scripts/seed_content.py` runs. Need a context-managed "bulk mode" flag to skip during seeding (matches Risk row "Re-embedding cascade on bulk updates").
