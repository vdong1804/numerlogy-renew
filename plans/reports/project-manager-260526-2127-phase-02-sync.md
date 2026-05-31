# Phase 02 Sync Report — Post-Review Fixes Applied

**Date:** 2026-05-26 21:27  
**Plan:** `plans/260526-1854-chatbot-rag-pdf-analysis/`  
**Summary:** Phase 02 (Core Chat) moved from code-complete → complete after applying 4 critical post-review fixes + 3 new tests. All 51/51 tests passing.

---

## What Was Updated

### phase-02-core-chat-retrieval.md Changes

**Status line:** `code-complete (2026-05-26)` → `complete (2026-05-26)` (lines 9-10)

**Added "Post-Review Fixes Applied" section** (new, after Todo List):
- **C1 Fix:** User message persistence on LLM 502. Split INSERT into two transactions: user msg commits first (releases locks), then LLM call, then assistant msg. Prevents rollback loss.
- **C2 Fix:** LLM timeout with HTTP bounds. Added `httpx.Timeout(total=30)` to genai.Client. Stops thread-pool leak on repeated timeouts (was only `asyncio.wait_for` before).
- **H8 Fix:** Retrieval failure short-circuit. Skip LLM when retrieval errors; return canonical "Tôi không có đủ thông tin..." directly via `_persist_and_return_canonical` helper. Saves cost + gives ops clear signal.
- **H12 Fix:** Empty LLM response guard. `LlmService.generate` raises `LlmError` if `resp.text` empty (safety-blocked). No blank bubbles.

**New tests added:**
- `test_system_prompt_contains_canonical_no_info_phrase` — validates system prompt contract.
- `test_retrieval_failure_short_circuits_to_canonical` — E2E coverage for H8.
- `test_user_message_persists_on_llm_error` — validates C1 transaction split.

**Test tally:** 51/51 passing (was 48/48 before fixes).

### plan.md Changes

**Phase 02 row:** `code-complete (2026-05-26)` → `complete (2026-05-26)` (line 30)

**Overall status unchanged:** `in-progress (2/8 phases complete)` — Phase 01 was already complete, Phase 02 now also complete.

---

## Current Project State

| Phase | Status | Notes |
|-------|--------|-------|
| 01 | complete | Foundation (DB schema, embedding service, KB ingest) |
| 02 | complete | Core chat (retrieval, endpoint, citations) + post-review fixes |
| 03–08 | pending | User PDF, streaming UI, quota, cache, admin tuning, hardening |

**Overall:** 2/8 phases done (25%). Phase 01 + 02 form the RAG backbone; Phases 03–08 layer user features + ops.

---

## Phase 03 Readiness (User PDF Hybrid)

**Does Phase 03 have what it needs from Phase 02?** YES, with 1 clarification needed.

### What Phase 03 depends on from Phase 02:
1. **`RetrievalService.retrieve()`** interface — stable. Phase 03 will call `retrieve(pdf_context_id=...)` to fetch user PDF chunks alongside KB chunks. Phase 02 has the hook parameter ready (accepted, threaded, currently unused).
2. **System prompt + citation format** — stable. Phase 03 will reuse both.
3. **`LlmService` non-streaming** — stable. Phase 03 orchestrates hybrid retrieval (KB + user PDF top-k merge) but reuses the same LLM call.
4. **Message/conversation CRUD** — stable. Phase 03 adds `POST .../upload-pdf` + `DELETE .../pdf-context` endpoints; re-uses existing conversation flows.

### Cross-reference scan (Phase 03 file):

- ✓ Imports Phase 02 `RetrievalService` interface correctly (mentions `pdf_context_id` parameter).
- ✓ Schema shows `ALTER TABLE chat_conversations ADD CONSTRAINT ... REFERENCES user_pdf_index(id)` — FK already declared in Phase 01 DB but no table yet (Phase 03 creates it).
- ✓ No conflicts with Phase 02 code paths. Phase 03 adds new tables + new router `/upload-pdf`, doesn't modify Phase 02 routes.

### Unresolved for Phase 03 planning:

1. **Hybrid merging strategy:** Phase 03 plan says "rebalance, e.g. 2 KB + 3 PDF for free" but doesn't specify: is this hardcoded in `retrieve()` logic, or a separate merging service? Phase 02 returns `list[RetrievedChunk]` with a `source_type` field — Phase 03 will need to split by type and rebalance. Minor but should be clarified in Phase 03 implementation plan.

---

## Phase 04 Cross-Reference Check (Streaming UI)

**Depends on:** P2 (LLM service) + P3 (PDF upload UI hook)

- ✓ Phase 04 references Phase 02's `LlmService` + `generate()` method. C2 fix (HTTP timeout) makes P04's streaming endpoint safer.
- ✓ Phase 04 backend adds `POST .../messages/stream` endpoint. Reuses existing `RetrievalService`, `prompt_builder`, citation parser — all Phase 02.
- ⚠️ **Note:** Phase 04 streaming will need to revisit the C1 fix (transaction model). Current Phase 02 design commits user message first, then runs LLM in a separate session. For SSE streaming, Phase 04 will need to decide: **commit user message before opening the stream, or after stream closes?** This is an open question from the code review but Phase 02 answer (split transactions) works for both models.

---

## Outstanding Code Review Follow-Ups

**Must-Fix items from code review (not yet closed as tasks):**
- [ ] C1: Transaction strategy documented + implemented ✓ (fixed in Phase 02)
- [ ] C2: HTTP timeout bounds ✓ (fixed in Phase 02)
- [ ] H8: Retrieval failure short-circuit ✓ (fixed in Phase 02)
- [ ] H12: Empty response guard ✓ (fixed in Phase 02)

**Should-Fix (cleanup tickets, Phase 02 scope but deferred):**
- [ ] H6: Extract `resolve_tier(user)` helper for Phase 05 quota prep
- [ ] H7: Make `pdf_context_id != None` raise `NotImplementedError` until Phase 03 wires it
- [ ] H11: Document `chunk_id` privacy stance; plan Phase 03 separation
- [ ] H14, H15: 5 missing test coverage items (empty KB, hallucinated index, multi-turn history, retrieval failure)
- [ ] H17: Cache `EmbeddingService` + `LlmService` to reuse HTTP connections

**Recommendation:** File these 5 as explicit cleanup tasks in the next sprint. They don't block Phase 03 parallel work but should be resolved before Phase 05 (quota) to avoid "forgot one of three tier-hardcoded places" bugs.

---

## Unresolved Questions

1. **Phase 03 hybrid merge logic:** Where does rebalancing (e.g., 2 KB + 3 PDF for free) live — in `RetrievalService.retrieve()` or a separate service? Impacts Phase 03 design.
2. **Phase 04 SSE transaction timing:** User message commit before stream opens or after? Phase 02's split-transaction design works for both but Phase 04 should formalize the choice early to avoid surprises.
3. **Should-Fix cleanup tasks:** Are H6 (tier helper), H7 (pdf_context_id guard), H11 (privacy stance), H14/H15 (test coverage) prioritized for Phase 02 sprint, or deferred to Phase 05 backlog?
