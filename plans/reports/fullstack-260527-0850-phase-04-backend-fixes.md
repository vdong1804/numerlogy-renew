# Phase 04 Backend Fixes Report

## Status: completed

---

## Files Modified

| File | Change |
|------|--------|
| `app/schemas/chat/message.py` | +1 field `pdf_context_id: Optional[int]`; removed unused `Optional` import where possible; `# noqa: UP045` for Py3.9 compat |
| `app/services/chat/chat_turn.py` | +18 LOC: new `persist_no_info_assistant()` helper |
| `app/routers/chat/_stream_generator.py` | NEW file, 120 LOC: extracted `generate_sse_events()` async generator |
| `app/routers/chat/messages.py` | -100 LOC net (282→185): uses new helper + extracted generator; applies pdf_id override |
| `app/services/chat/llm_service.py` | +14 LOC: H2 docstring + `CancelledError` re-raise in consumer loop + `_call` |
| `app/services/chat/sse_formatter.py` | -4 LOC: removed dead `DONE_SENTINEL_KEYS` constant |

---

## Fixes Applied

### Fix #1 — C1: `MessageIn` accepts `pdf_context_id`
- `app/schemas/chat/message.py:11`
- Before: `content: str = Field(...)` only
- After: `pdf_context_id: Optional[int] = None`
- Both `send_message` and `generate_sse_events` now compute: `pdf_id = body.pdf_context_id if body.pdf_context_id is not None else conv.pdf_context_id`

### Fix #2 — M2: shared `persist_no_info_assistant` helper
- `app/services/chat/chat_turn.py` after `run_retrieval`
- Before: inline `ChatMessage(...)` + `db.add/flush/refresh` duplicated in both paths
- After: single `persist_no_info_assistant(db, conversation_id, text) -> ChatMessage`; `_persist_and_return_canonical` and stream no-info branch both call it

### Fix #3 — M3: extract stream event generator
- New file `app/routers/chat/_stream_generator.py` (120 LOC)
- `generate_sse_events(db, conv, user_msg, body, llm)` is top-level, importable
- `messages.py` drops from 282 → 185 LOC (well under 220 target)

### Fix #4 — M4: re-raise `CancelledError`
- `app/services/chat/llm_service.py` consumer loop + `_call`
- Before: `except Exception` in consumer caught everything including `CancelledError`
- After: `except asyncio.CancelledError: raise` before generic catch in both `generate_stream` and `_call`
- `_stream_generator.py` also has `except asyncio.CancelledError: raise` before its `except Exception`
- Note: `_producer` thread's `except Exception` left as-is — correct, `CancelledError` does not propagate into daemon threads

### Fix #5 — H2: docstring on `generate_stream`
- `app/services/chat/llm_service.py:106-111`
- 4-line NOTE added to existing docstring documenting: producer cannot be force-killed, `HttpOptions(timeout=...)` bounds worst-case, cancellation stops consumer only
- No code change — google-genai sync iterator checked; no `.close()` hook exposed on `generate_content_stream` return type

### Fix #6 — Low: remove dead `DONE_SENTINEL_KEYS`
- `app/services/chat/sse_formatter.py`
- Before: `DONE_SENTINEL_KEYS = ("message_id", "input_tokens", "output_tokens", "model_used")`
- After: removed; confirmed zero imports/usages across codebase

### Fix #7 — Low: drop hard-coded model fallback
- `app/routers/chat/_stream_generator.py:90`
- Before: `stream_result.model_used or "gemini-2.0-flash"`
- After: `stream_result.model_used or llm.model_id("flash")`

---

## Test Results

```
13 passed, 3 warnings in 8.33s
```
All 13 chat tests pass (happy path × 7, retrieval failure × 1, LLM error × 2, ownership × 3).

---

## Lint Results

```
ruff check  — All checks passed!
ruff format — 6 files already formatted
```

Note: `Optional[int]` used instead of `int | None` in `message.py` (Python 3.9 + Pydantic 2.10.4 without `eval_type_backport` cannot evaluate `X | None` union syntax at runtime even with `from __future__ import annotations`). Suppressed with `# noqa: UP045` on the 4 `Optional[...]` fields in that file.

---

## Deviations

- `message.py` type annotations: ruff UP045 wants `X | None`; kept `Optional[...]` + noqa due to Py3.9 Pydantic runtime constraint. Pre-existing `Optional[str]` fields also suppressed for consistency.
- H1 (DB pool refactor): not implemented per scope — accepted risk, document in H1 section of review.

---

## Skipped (out of scope)

- H1 DB connection pool refactor — accepted; pool sizing recommendation deferred
- H6 JWT refresh on stream 401 — frontend concern
- M5 additional tests — separate test pass
- Nginx changes (M7/M8) — ops concern

---

## Unresolved

1. `eval_type_backport` not installed — if team upgrades to Python 3.10+ or installs that package, `# noqa: UP045` suppressions in `message.py` can be removed and `X | None` used consistently.
2. H2 producer thread leak on cancel — intrinsic to sync SDK bridge pattern; `HttpOptions(timeout=...)` is the only bound. No SDK `.close()` hook found on `generate_content_stream`.
