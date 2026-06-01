# Code Review — DeepSeek LLM Migration

**Scope:** `numerology-api/` working-tree vs HEAD on `master`.
**Diff:** 23 files, +279/-1172 LOC. Cleanly subtractive.

## Summary

The migration is well-scoped and correct. `LlmService` rewrite is clean, the
stream-usage parsing matches the DeepSeek/OpenAI `include_usage` contract, the
prompt-cache removal is thorough (zero leftover references in `app/`), and the
single-model strategy is preserved at the API boundary via accepted-and-ignored
kwargs. Migration `a1d6e2c84f31` correctly chains off the initial schema head
and is safe against production data (drops a table that holds only
short-TTL'd cache pointers).

**One blocking issue:** the admin analytics frontend reads
`prompt_cache_active_handles.toLocaleString()` on a field that this PR removes
from the dataclass — silent breaking change to an existing API contract. The
admin page will crash with `TypeError` on load. Frontend changes are out of
scope per the brief, but flagging because it's a direct consequence of this
backend change.

Everything else is minor (stale docstrings, an inherited error-leak in the SSE
path, etc.).

---

## Critical findings (must-fix)

### C1. Admin analytics dropped field breaks frontend
- `app/services/chat/chat_analytics_service.py` removes `prompt_cache_active_handles` from `AnalyticsOverview`.
- Frontend still consumes it:
  - `Numerology-Landing-Page/src/modules/admin/chatbot/chatbot-types.ts:127` types it as `number` (non-optional).
  - `Numerology-Landing-Page/src/pages/admin/chatbot/analytics.tsx:149` calls `.toLocaleString()` directly: `data?.prompt_cache_active_handles.toLocaleString() ?? '—'`.
- The `data?.` only guards the parent — `.toLocaleString()` on `undefined` still throws.
- **Fix options** (pick one):
  1. Keep `prompt_cache_active_handles: int = 0` in the dataclass (zero-valued legacy field) for one release window, then deprecate after FE catches up.
  2. Coordinate a same-PR FE removal of the type + UI stat block.
- Recommend option 1 — keeps deploy independent and avoids cross-repo coupling.

---

## Major findings

### M1. SSE error path leaks upstream DeepSeek error details
- `app/routers/chat/_stream_generator.py:218` yields `{"code": ..., "message": str(exc)}` for any non-`CancelledError` exception.
- For `LlmError`, `str(exc)` is `"LLM call failed: <openai.APIError str>"` or `"LLM stream failed: ..."`. The wrapped openai exception string can include the request URL, response body fragments, and provider-specific error codes.
- The non-streaming send path (`messages.py:228-231`) already returns a sanitized `"Vui lòng thử lại sau giây lát."` — apply the same redaction to the SSE branch:
  ```python
  user_msg = "Vui lòng thử lại sau giây lát." if isinstance(exc, LlmError) else "internal error"
  yield sse_event("error", {"code": code, "message": user_msg})
  ```
- **Note:** this is *pre-existing* on HEAD (already there before the migration), so not strictly a regression. But the salience changes — DeepSeek's error envelopes differ from Gemini's, and the migration is the right moment to clean it up.

### M2. Stale docstring in `prompt_settings_service.py`
- Line 7 still references "keeping Gemini's explicit prompt cache stable for the common case." This contradicts the new line 19-20 paragraph and is misleading for future maintainers.
- Update lines 5-8 to drop the Gemini cache reference.

### M3. Stale module-level docstring in `tests/routers/chat/test_messages.py`
- Line 4: `"...the test never touches pgvector or the real Gemini API."` — provider name should be DeepSeek (or generic "the real LLM"). The streaming test was updated (line 4 in `test_stream_endpoint.py` correctly says DeepSeek). Just a one-word fix.

---

## Minor / nice-to-have

### m1. `flash_model` / `pro_model` back-compat kwargs
- `LlmService.__init__` accepts `flash_model` and `pro_model` purely so existing test code keeps working. The production callers (`messages.py:219`, `messages.py:319`) construct `LlmService()` with no kwargs, so this code path is only exercised by `tests/services/chat/test_llm_service.py:188`.
- Grep confirms zero production callers pass these. This is YAGNI-adjacent: the only reason to keep the shim is the one explicit test that *verifies* the shim. Either delete the kwargs and that one test (cleaner) or keep both (current state — defensible if you expect external callers).
- **Recommendation:** keep as-is for one release window, then remove. Not blocking.

### m2. `LlmError` constructor includes raw exception in message
- `f"LLM call failed: {exc}"` and `f"LLM stream failed: {exc}"` pull the openai exception's `__str__` into the LlmError text. Combined with M1 above, this is the leak vector. If you redact at the SSE boundary (M1 fix), this becomes harmless — the raw text stays in logs (where it belongs) and the client gets the sanitized message.

### m3. `cleanup_semantic_cache` log line redundant key
- Line 28: `logger.info("cleanup_semantic_cache: semantic_cache=%d deleted", sem_deleted)` — the job name already prefixes; the `semantic_cache=` label is redundant now that there's only one counter. Stylistic.

### m4. Test stubs still use `gemini-2.0-flash` as a mock `model_used`
- `tests/routers/chat/test_messages.py:62`, `tests/routers/chat/test_stream_endpoint.py:101,278`. These stubs are validating that legacy model strings flow through to persistence, which is actually *desired* behavior (PRICING dict retains the Gemini keys for legacy rows). No change needed — calling it out so reviewers don't "fix" it.

---

## Verified clean

- **No leftover references** in `numerology-api/`:
  - `PromptCache`, `prompt_cache_service`, `cached_content`, `invalidate_for_chunks`, `gemini_flash_model`, `gemini_pro_model`, `prompt_cache_hit_threshold`, `prompt_cache_ttl_seconds` — all return zero grep hits in `app/`, `tests/`, and `scripts/`.
- **`prompt_cache_handles`** table is referenced only in alembic migration files (`497b2cb25f8d_initial_schema.py` creates, `a1d6e2c84f31_drop_prompt_cache_handles.py` drops). No model, service, or query references it.
- **`PromptCacheHandle`** symbol — zero grep hits anywhere in `numerology-api/`.
- **LlmService stream usage parsing** — correctly handles the DeepSeek/OpenAI contract where the final usage-only chunk has `chunk.choices == []` and `chunk.usage` populated. `if chunk.choices:` guards delta extraction; `usage = getattr(chunk, "usage", None)` reads tokens unconditionally. Earlier chunks have `usage=None` per the SDK spec — the falsy check at line 136 keeps result clean.
- **`stream_options={"include_usage": True}`** is set at line 125. Verified.
- **Error mapping** — `APIError`, `APIConnectionError`, `APITimeoutError` all wrap into `LlmError` (lines 139-142, 164-167). `asyncio.CancelledError` is re-raised both in `generate_stream` (line 143-144) and `generate` (line 168-169). Tests cover all three.
- **Empty-text guard preserved** in `generate()` at lines 172-174 — raises `LlmError("LLM returned empty response (likely safety filter)")` instead of persisting a blank assistant bubble.
- **`model_id(tier)`** returns `self._chat_model` regardless of tier — single-model strategy correctly applied (line 90-93). `_stream_generator.py:159` uses this as a fallback when the stream finishes without a `model_used` field — safe.
- **`kb_sync.py` after_commit hook** — flushes `_PENDING_KEY` from session.info onto the asyncio queue. Removal of `invalidate_for_chunks_sync` is clean — the docstring is updated (line 77-79), and the worker still processes upsert/delete actions correctly. No dead code left.
- **`cleanup_semantic_cache.py`** — return shape `{"semantic_cache": N}` is exactly what tests assert (`set(result.keys()) == {"semantic_cache"}` on test line 168).
- **`aggregate_chat_metrics.py`** — `calc_msg_cost(str(model_used), ...)` now uses the raw `model_used` column value. Legacy Gemini rows still resolve via the PRICING dict's preserved Gemini entries; new rows resolve to `deepseek-chat`. Unknown models → `0` with a warning (`cost_monitor_service.py:60-62`). Correct.
- **`cost_monitor_service.PRICING`** — DeepSeek-chat entry uses correct rates per scope ($0.27/Mtok input, $1.10/Mtok output, $0.07/Mtok cached_input). Gemini entries kept verbatim for historic rows.
- **`chat_analytics_service.MODEL_PRICING`** — covers both providers. `_DEFAULT_PRICE = (0.27, 1.10)` (DeepSeek rates) is a reasonable fallback for unknown models.
- **`config.py`** — `gemini_api_key` and `embedding_model` retained (embeddings remain on Gemini per scope). New `deepseek_*` block is well-organized. Removed fields (`gemini_flash_model`, `gemini_pro_model`, `prompt_cache_hit_threshold`, `prompt_cache_ttl_seconds`) — zero downstream readers (verified by grep).
- **Alembic migration `a1d6e2c84f31`**:
  - `down_revision = '497b2cb25f8d'` correctly points to the current (and only other) head.
  - `op.drop_table('prompt_cache_handles')` is safe — initial migration creates this table, so it's guaranteed present on any deployed DB.
  - Downgrade re-creates the empty schema — historical rows are unrecoverable but had no business value (short-TTL'd Gemini cache pointers).
- **`pyproject.toml`** — `openai>=1.40,<2` added. Major-version pin keeps us off the SDK 2.x line until a deliberate bump.
- **`.env.example`** — old Gemini chat vars removed, DeepSeek block added with clear sourcing instructions. Both the embedding-only Gemini block and the DeepSeek chat block are kept side-by-side.
- **`app/db/models/chat/__init__.py`** — `PromptCacheHandle` removed cleanly from imports and `__all__`. Alembic autogenerate will see consistent metadata.
- **Deleted files** — `prompt_cache_service.py`, `prompt_cache_handle.py` (model), and the associated test file are all gone. No phantom imports.
- **Test coverage** — `tests/services/chat/test_llm_service.py` (new) covers happy path, empty-response, APIError/APITimeoutError/APIConnectionError wrapping, missing-API-key guard, `model_id()` single-model semantics, and the back-compat kwargs. Stream test verifies `stream_options={"include_usage": True}` is passed and the empty-`choices` final chunk populates `StreamResult`.

---

## Unresolved questions

1. **Frontend coordination for `prompt_cache_active_handles`** — should the backend ship the zero-valued legacy field (option 1 in C1) or block this PR pending FE update? Lead's call.
2. **SSE error redaction (M1)** — pre-existing leak. Is this PR the right place to fix it, or should it be tracked separately?
3. **`flash_model` / `pro_model` shim lifetime (m1)** — when do we want to delete these kwargs entirely? Suggest tagging for removal one release after FE confirms no external callers.

---

**Status:** DONE_WITH_CONCERNS
**Summary:** Migration is correct and YAGNI-clean inside `numerology-api/`; one frontend-coupling field (`prompt_cache_active_handles`) silently breaks the admin analytics page and needs coordinated handling.
