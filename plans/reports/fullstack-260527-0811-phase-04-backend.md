# Phase 04 Backend — SSE Streaming Endpoint

**Date:** 2026-05-27
**Status:** completed

---

## Files Created/Modified

| File | LOC | Action |
|------|-----|--------|
| `app/services/chat/sse_formatter.py` | 33 | created |
| `app/services/chat/chat_turn.py` | 97 | created (split from messages.py to stay ≤200 LOC) |
| `app/services/chat/llm_service.py` | 222 | modified (+83 LOC: StreamResult dataclass + generate_stream) |
| `app/routers/chat/messages.py` | 222 | modified (rewritten to use chat_turn helpers + stream endpoint) |
| `tests/routers/chat/test_stream_endpoint.py` | 234 | created |
| `.env` | — | fixed pre-existing encoding bug (UTF-8 BOM/smart-quotes → ASCII-safe) |

---

## SSE Event Schema Emitted

```
event: delta
data: {"token": "<text chunk>"}

event: delta
data: {"token": "...more tokens..."}

event: citations
data: {"citations": [{"index": 1, "chunk_id": 101, "document_id": 11,
       "source_type": "numerology:mission_number", "source_ref": "MN_1",
       "title": "T1", "score": 0.9}]}

event: done
data: {"message_id": 42, "input_tokens": 50, "output_tokens": 12,
       "model_used": "gemini-2.0-flash"}

event: error
data: {"code": "llm_error"|"internal_error", "message": "<str>"}
```

All JSON uses `ensure_ascii=False` — Vietnamese text is preserved as-is.

---

## Implementation Notes

### `sse_formatter.py`
Single function `sse_event(event, data) -> bytes`. No class, no state.
Ruff auto-removed the redundant `encoding="utf-8"` arg from `.encode()`.

### `chat_turn.py` (new module)
Extracted because `messages.py` would have reached ~260 LOC with stream endpoint inline.
Contains: `persist_user_message`, `run_retrieval`, `build_turn_prompt`, `persist_assistant_message`.
Both sync and stream endpoints import from here — zero logic duplication.

### `llm_service.py` changes
- Added `StreamResult` dataclass (sidecar for token counts after stream exhausted).
- Added `generate_stream(system, user_content, tier, result) -> AsyncIterator[str]`.
- Bridge pattern: `threading.Thread` runs sync SDK iterator; puts chunks onto `asyncio.Queue`
  via `loop.call_soon_threadsafe`; async consumer `await asyncio.wait_for(queue.get(), timeout)`.
- First-token timeout: `asyncio.wait_for` with `self._timeout` applies only to the first item;
  subsequent items have no per-token timeout (stream may have natural pauses).
- Token counts written to `result.input_tokens/output_tokens` from `usage_metadata` on last chunk.
- `generate()` (non-streaming) unchanged.

### `messages.py` stream endpoint
- `send_message` now delegates all shared logic to `chat_turn.*` helpers.
- `stream_message` uses `_event_gen()` async generator, wrapped in `StreamingResponse`.
- Ownership check + user message persist happen BEFORE the generator starts — so 404/422 are normal HTTP responses (not SSE errors).
- Retrieval failure short-circuit: emits single `delta` with `NO_INFO_VI`, persists canonical assistant row, emits `done`. LLM not called.
- Mid-stream `LlmError` → emits `event: error` with `code: "llm_error"`. No broken assistant message committed (accumulation buffer never flushed to DB if error occurs before `persist_assistant_message`).
- `_SSE_HEADERS` constant: `X-Accel-Buffering: no`, `Cache-Control: no-cache`, `Connection: keep-alive`.

---

## Test Results

```
40 passed, 3 warnings in 26.33s
```

- 13 new stream tests (all pass)
- 27 existing chat tests (all still pass — no regression)
- Warnings: pre-existing `event_loop` deprecation in conftest (pytest-asyncio 0.25) + google-auth Python 3.9 EOL notice — neither is introduced by this phase.

### Test coverage by class
| Class | Tests |
|-------|-------|
| `TestStreamEndpointHappyPath` | 7 (status, delta events, citations, done, persistence, event order, UTF-8) |
| `TestStreamRetrievalFailure` | 1 (retrieval fail → no-info delta + done, LLM not called) |
| `TestStreamLlmError` | 2 (error event emitted, no broken assistant message) |
| `TestStreamOwnership` | 3 (404 non-owner, 401 unauth, 422 empty content) |

---

## Lint Output

```
ruff check: All checks passed!
```

16 issues auto-fixed by `ruff --fix` (UP045 Optional→X|None, UP035 AsyncIterator import,
UP041 asyncio.TimeoutError→TimeoutError, I001 import sort, F401 unused import, UP012 encode arg).

---

## Manual SSE Smoke Test (no live API key needed to document)

```bash
# Obtain token first
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass"}' | jq -r .access_token)

# Create conversation
CONV_ID=$(curl -s -X POST http://localhost:8000/api/chat/conversations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"test"}' | jq .data.id)

# Stream endpoint (curl -N disables output buffering)
curl -N -X POST "http://localhost:8000/api/chat/conversations/$CONV_ID/messages/stream" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Số đường đời 7 có ý nghĩa gì?"}'
```

Expected output:
```
event: delta
data: {"token":"Số "}

event: delta
data: {"token":"đường "}

...

event: citations
data: {"citations":[...]}

event: done
data: {"message_id":1,"input_tokens":1200,"output_tokens":300,"model_used":"gemini-2.0-flash"}
```

---

## Deviations from Phase Spec

| Spec | Actual | Reason |
|------|--------|--------|
| Phase spec shows `generate(..., stream=True)` signature | Implemented as `generate_stream(...)` separate method | Keeps non-streaming `generate()` unchanged; cleaner type signatures |
| No mention of `chat_turn.py` split | Created `chat_turn.py` | `messages.py` would reach ~260 LOC; spec explicitly says "split if grows beyond 200 → `chat_turn.py` or similar" |
| Phase spec says `ensure_ascii=False` in SSE JSON | Done; ruff removed redundant `encoding="utf-8"` arg from `.encode()` (bytes default to UTF-8 anyway) | No semantic change |

---

## Pre-existing Issue Fixed (side effect)

`.env` file had UTF-8 smart-quotes (`"`) and euro sign (`€`) in a comment line. Starlette's
`Config._read_file` uses `open()` without `encoding=` — on Windows defaults to cp1252 which
cannot decode those bytes. This blocked ALL tests on this machine. Fixed by replacing
non-ASCII chars in the comment line with ASCII equivalents. Values (JWT_SECRET etc.) were
unaffected — all ASCII.

---

## Unresolved Questions

1. `generate_stream` first-token timeout applies `self._timeout` (default from `settings.llm_timeout_seconds`). Subsequent token gaps have no per-token timeout — if the API stalls mid-stream after the first token, the generator will hang until the connection is closed by nginx (300s). Is a per-token watchdog needed, or is nginx `proxy_read_timeout 300s` sufficient?

2. On mid-stream `LlmError`: the partial accumulated text is discarded (no assistant message persisted). The user sees the `event: error` but the partial tokens they already received in the browser are orphaned. Should the endpoint persist a partial assistant message with an `error` state flag? Current behavior: no broken row in DB (clean), but partial tokens shown in UI have no DB record.

3. `StreamResult.model_used` is set to `model_id` at the start of `generate_stream`. If the SDK returns a different `model` field in the response (e.g. routing to a different model version), we don't capture that. Is the SDK's response model field accessible on stream chunks?
