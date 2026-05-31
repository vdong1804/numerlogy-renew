# Phase 04 Code Review

## Summary
- Overall: **pass with required fixes**
- Critical: 2
- High: 6
- Medium: 8
- Low: 7

Streaming wire contract is sound, ownership/auth enforced, no obvious XSS/injection. Two contract bugs that silently degrade UX: (a) `MessageIn` schema ignores the FE-sent `pdf_context_id` body field, (b) FE `Citation` type is missing `documentId`/`sourceRef` (drops from `toMessage()` map). One real resource leak via held DB connection during the entire stream. Producer thread cancellation is incomplete on client abort.

---

## Critical

### C1. FE-sent `pdf_context_id` in stream body is silently dropped
**File:** `numerology-api/app/schemas/chat/message.py:9-10` + `Numerology-Landing-Page/src/modules/chat/hooks/use-chat-stream.ts:110-113`
**Issue:** `MessageIn` only declares `content`; Pydantic default extras=ignore. FE sends `{ content, pdf_context_id }` — `pdf_context_id` is dropped. Endpoint then uses `conv.pdf_context_id` from the conversation row (set at upload time). Net behavior: passing `pdf_context_id` from FE has zero effect; whichever PDF was last attached via `POST /upload-pdf` or `PATCH /pdf-context` is used.

This is not currently exploitable (upload auto-attaches), but creates two failure modes:
1. User uploads PDF A → attaches it → user clears via `usePdfUpload.clear()` (FE-only state, no PATCH) → next send keeps using PDF A from DB. The "removed" pill in UI lies.
2. If/when multi-PDF attach is added, the FE contract suggests it works but doesn't.

**Fix:** pick one path and document it. Recommended:
```python
class MessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    pdf_context_id: int | None = None  # explicit override; falls back to conv.pdf_context_id
```
Then in `send_message`/`stream_message`:
```python
pdf_id = body.pdf_context_id if body.pdf_context_id is not None else conv.pdf_context_id
chunks, retrieval_ok = await run_retrieval(db, body.content, pdf_id)
```
AND `PdfUploadButton.onRemove` should call `DELETE /api/chat/conversations/{id}/pdf-context` so DB state matches UI.

### C2. FE `Citation` type missing `documentId`/`sourceRef` — fields are lost on completed-message render
**File:** `Numerology-Landing-Page/src/models/Chat.ts:13-19` + `src/modules/chat/api/chat-api.ts:98-104`
**Issue:** Backend `Citation` serializes `{ index, chunk_id, document_id, source_type, source_ref, title, score }`. FE `Citation` type and `toMessage()` mapper read only `{ index, chunk_id, source_type, title, score }`. `document_id` and `source_ref` are dropped silently on the REST path.

Streaming path is worse: `use-chat-stream.ts:152-154` does `finalCitations = citations` from the SSE `citations` event WITHOUT running it through `toMessage()` or any snake→camel transform. So during a live stream, `streamingCitations[0]` is shaped `{ chunk_id, source_type, source_ref, document_id, ... }` (snake_case from server), but after the message is persisted and rehydrated via `listMessages`, the same data is `{ chunkId, sourceType, title, score }` (camelCase, missing fields).

Result: `CitationDrawer` reads `citation.chunkId` (correct on persisted messages) and `citation.sourceType` (correct), but **during streaming** `streamingCitations` rows have `chunk_id`/`source_type` not `chunkId`/`sourceType` → drawer shows blank chunk id + blank source type for live citations. Click `[1]` mid-stream → broken drawer. Reload → drawer works.

**Fix:** add a `toCitation()` mapper and apply it on the SSE path:
```ts
// chat-api.ts — export
export function toCitation(r: CitationRaw): Citation { ... }

// use-chat-stream.ts handleFrame, 'citations' branch:
const { citations } = parsed as { citations: CitationRaw[] }
const mapped = citations.map(toCitation)
finalCitations = mapped
setStreamingCitations(mapped)
```
And extend `Citation` type with `documentId: number` and `sourceRef: string` so both transports carry the same shape.

---

## High

### H1. DB connection held for entire stream duration
**File:** `numerology-api/app/routers/chat/messages.py:188-282`
**Issue:** `get_db` yields the session for the whole request. In sync `send_message`, `persist_user_message` commits before LLM call, so the session is idle but the connection is still leased from the pool until response return. In `stream_message`, the situation is the same connection-wise, but the lease lasts **the entire token stream duration** (potentially 30+ seconds). At pool size N, concurrent streams = N → all subsequent chat requests block.

Worse: `await db.commit()` after retrieval is missing. After `persist_user_message` commits, we then call `run_retrieval` (a SELECT — fine), then `build_turn_prompt` (another SELECT), then `persist_assistant_message` + `await db.commit()`. So the conn IS leased the whole time even though it's idle waiting for tokens.

**Likelihood:** moderate. Pool default is small (typically 5–20). With 5–10 concurrent stream users you exhaust the pool. Other endpoints hang.

**Fix options (pick one):**
1. Cheapest: After committing user message, explicitly release the connection: `await db.close()` and reopen a new session for the post-stream persist step. This is awkward with FastAPI's dep injection.
2. Better: refactor to take a `sessionmaker` dep instead of a session — open short-lived sessions around each DB touch (commit user, persist assistant). Keep zero open connections during the LLM stream window.
3. Document accepted risk and bump pool size proportional to expected concurrent streams.

### H2. Producer thread cannot be cancelled on client disconnect
**File:** `numerology-api/app/services/chat/llm_service.py:115-167`
**Issue:** On client abort (FE calls `ctrl.abort()`), FastAPI cancels the awaited `queue.get()`. The async iterator's `finally` runs `thread.join(timeout=1)` — but the SDK call `for chunk in stream:` is blocking on a socket inside the thread. `thread.join(timeout=1)` returns after 1s without stopping the producer. The thread continues consuming tokens for the full LLM response (10–30s), and `loop.call_soon_threadsafe` keeps trying to schedule items on a queue nobody reads. The thread is daemon so it dies on process exit, but you still pay 10–30s of LLM cost + socket + thread for every cancelled request.

`asyncio.wait_for(queue.get(), timeout)` cancellation propagates to the consumer only — the SDK thread keeps running independently.

**Fix:** thread the SDK iterator's lifecycle through a cancel signal:
```python
cancel_event = threading.Event()

def _producer():
    try:
        for chunk in stream:
            if cancel_event.is_set():
                stream.close() if hasattr(stream, 'close') else None
                return
            ...
```
And set it from the consumer's `finally`. Note: google-genai sync iterator may not have a usable `.close()`; check SDK. Without SDK-level cancel, document the leak as accepted and rely on http timeout in `genai_types.HttpOptions(timeout=...)` to upper-bound it.

### H3. Stream `finally` flushes state — but `streamingCitations` is cleared before parent renders the persisted message
**File:** `Numerology-Landing-Page/src/modules/chat/hooks/use-chat-stream.ts:215-221`
**Issue:** The `finally` block runs `setStreamingText('')` + `setStreamingCitations([])` + `setIsStreaming(false)` synchronously. `onMessageComplete(completedMessage)` was called inside `try` BEFORE finally. React batches state updates → the next render sees:
- New persisted message in `messages` (via `append`)
- Empty `streamingText` and `streamingCitations`
- `isStreaming = false`

This is the intended outcome. BUT: `handleCitationClick` in `ChatLayout.tsx:89-101` looks up citations from both `streamingCitations` and `messages.flatMap(m => m.citations)`. After completion, `streamingCitations` is empty (correct) AND the persisted message's citations come from `onMessageComplete` — which uses `finalCitations` from the SSE event (raw snake_case from C2). So `messages[last].citations[0].chunkId` is `undefined` until the user navigates away and back (re-listing rehydrates via `toMessage`).

This is the **second leg of C2** — same root cause. Fix C2 and this clears up.

### H4. Auto-scroll fights user scroll-up — no "user scrolled up" guard
**File:** `Numerology-Landing-Page/src/modules/chat/parts/MessageThread.tsx:122-124`
**Issue:** Every token triggers `bottomRef.current?.scrollIntoView({ behavior: 'smooth' })`. If the user scrolls up to re-read an earlier message mid-stream, every new token yanks them back to the bottom. Standard chat UX is: track "user has scrolled away from bottom" → suppress auto-scroll → show a "↓ new messages" button.

**Fix:** add a `nearBottomRef` derived from a scroll listener, only auto-scroll when within ~80px of bottom.

### H5. Recursive `pump()` accumulates stack frames per chunk
**File:** `Numerology-Landing-Page/src/modules/chat/hooks/use-chat-stream.ts:181-196`
**Issue:** `pump()` calls `await reader.read()` then `await pump()` recursively. Each call adds a stack frame in V8's microtask queue. For a 1000-token response with chunks of ~5 tokens each (200 frames), this is fine. For a 50000-token response with single-byte chunks, V8 doesn't optimize tail calls — you'll hit "Maximum call stack size exceeded" eventually.

Comment says it avoids `no-await-in-loop`/`no-restricted-syntax`. Better fix is to disable the lint for this one location:
```ts
// eslint-disable-next-line no-await-in-loop
while (true) {
  const { done, value } = await reader.read()
  if (done) break
  ...
}
```
Or use a `for await (const chunk of streamAsyncIterable(reader))` helper. Recursion here trades a real bug for a lint rule.

### H6. Auth token re-read on every send — no expiry check
**File:** `Numerology-Landing-Page/src/modules/chat/hooks/use-chat-stream.ts:83-87`
**Issue:** Token read from cookie at send-start; not validated for expiry. If a stream starts at second 0 and token expires at second 5, backend will 401 on… nothing actually, because the connection is already authenticated for the duration. So mid-stream JWT expiry won't kill the current stream (good), but the NEXT send will silently 401 → `throw new Error("Lỗi máy chủ: 401 ...")` → setError → user sees raw error. No refresh attempt.

`userFetch` from `lib/user-api` handles refresh on 401 (presumably — confirm), but `use-chat-stream.ts` uses raw `fetch()`, bypassing it. The `fetch()` was needed because `getReader()` requires manual handling.

**Fix:** on 401 from stream, attempt one silent refresh and retry, or redirect to `/login?next=/chat`. Currently any token-related error becomes a generic Vietnamese string.

---

## Medium

### M1. `dataLine` parsing fails on multi-line `data:` payloads
**File:** `Numerology-Landing-Page/src/modules/chat/hooks/use-chat-stream.ts:135-138`
**Issue:** Spec allows multiple `data:` lines per event (concatenated by `\n`). `parseFrame` only keeps the LAST `data:` line. Currently the backend never emits multi-line data — but if a `\n` ever ends up inside a token (JSON-encoded as `\n`, not literal newline, so fine), it works. If a payload exceeds some buffer, splitting could break. Low risk given backend emits one-line JSON.

### M2. `MessageOut.tier` in `_persist_and_return_canonical` doesn't match `_event_gen` no-info path
**File:** `numerology-api/app/routers/chat/messages.py:200-222`
**Issue:** Sync path uses `_persist_and_return_canonical()`. Stream path duplicates the assistant-row creation inline (lines 203-211). Duplication: `tier="free"` hard-coded in both, but `_persist_and_return_canonical` returns a populated `MessageOut` envelope while stream path emits only `message_id`. Drift waiting to happen.

**Fix:** extract a shared helper `persist_no_info_assistant(db, conversation_id, text) -> ChatMessage` and call from both. Avoids two-place edits.

### M3. Files exceed 200 LOC soft cap
- `MessageThread.tsx` — 204 LOC: borderline, sub-components inline. Could extract `SkeletonList` + `WaitingDots`.
- `ChatLayout.tsx` — 204 LOC: composition shell. Justified by orchestration role.
- `use-chat-stream.ts` — 228 LOC: parsing + state + abort. Borderline. Could extract `parseSseStream(reader)` async iterator.
- `llm_service.py` — 222 LOC: streaming + non-streaming together. Could split into `llm_service.py` + `llm_stream.py`.
- `messages.py` — 282 LOC (file actually 282, not 222 — backend report stale): clearly over. The 75-line `_event_gen` inner function is the bulk.

**Fix:** at minimum split `_event_gen` body into a top-level `async def _generate_sse_events(db, conv, user_msg, body) -> AsyncIterator[bytes]`. Drops `messages.py` to ~210.

### M4. `_event_gen` swallows `CancelledError` as generic exception
**File:** `numerology-api/app/routers/chat/messages.py:271-276`
**Issue:** `except Exception` catches `CancelledError` too (in Python 3.8+ it's `BaseException`, but FastAPI re-raises as `Exception` in some paths). On client disconnect, this emits `event: error` to a closed socket — harmless but logs a misleading "stream_message failed" stacktrace. Better:
```python
except CancelledError:
    raise  # let FastAPI handle the cancellation cleanly
except Exception as exc:
    ...
```

### M5. No test for partial token stream after first token (timeout edge)
**File:** `tests/routers/chat/test_stream_endpoint.py`
**Issue:** The 13 tests cover happy path, retrieval fail, instant LLM error, mid-stream LLM error, ownership. Missing:
- **First-token timeout**: `generate_stream` blocks forever on first item — does timeout fire and emit `event: error` cleanly?
- **Mid-stream pause** (Q1 from backend report): no per-token watchdog. No test covers this — could be left as accepted.
- **Empty token stream** (LLM returns no chunks): `if not accumulated: raise LlmError(...)` (messages.py:238-239) — covered? Not in the tests shown. Add: monkeypatch stream to yield nothing → expect `event: error` with `code: "llm_error"`.
- **Concurrent send to same conversation**: race between two `stream_message` calls, both committing assistant messages. No test, low priority.

### M6. `_streamingCitations` prefixed-unused parameter
**File:** `Numerology-Landing-Page/src/modules/chat/parts/MessageThread.tsx:115`
**Issue:** The `_streamingCitations` prop is passed but never used. Comment says "needed for future virtualization." YAGNI violation — remove the prop, re-add when virtualization lands. Currently it pollutes the type, the parent must compute it, and it's threaded through `ChatLayout.tsx:54,174`.

### M7. Nginx `location /api/chat/` disables buffering for ALL chat endpoints
**File:** `numerology-api/deploy/nginx.conf:117-139`
**Issue:** `proxy_buffering off` applies to `GET /api/chat/conversations` (list), `POST /api/chat/conversations` (create), `PATCH .../pdf-context`, etc. Buffering helps small JSON responses (single chunk to client). Loss is negligible — JSON is small — but it's not strictly correct.

**Fix (nice-to-have):**
```nginx
location ~ ^/api/chat/conversations/\d+/messages/stream$ {
    # SSE-only settings
    proxy_buffering off;
    ...
}

location /api/chat/ {
    # Default buffering for REST endpoints
    ...
}
```
Two locations needed; the regex location must be declared before the prefix one or with `^~` priority. Acceptable to defer.

### M8. `gzip off` in chat location vs `gzip on` globally — but `gzip` directive scope is `http, server, location` only when set
**File:** `numerology-api/deploy/nginx.conf:25, 133`
**Issue:** `gzip on` at http level applies to all responses. `gzip off` at the `location /api/chat/` level correctly disables for SSE (gzip buffers full response → kills streaming). Confirmed correct. But REST endpoints under `/api/chat/` also lose gzip — small effect, same root as M7.

---

## Low / Nits

- `sse_formatter.py:13` — `DONE_SENTINEL_KEYS` is exported but never used. Dead constant. Remove.
- `chat_turn.py:46` — type hint says "ok=False on any exception" but `tuple[list[RetrievedChunk], bool]` would be clearer as a NamedTuple/dataclass; minor.
- `llm_service.py:111` — `_DONE = object()` is fine, but a module-level sentinel would avoid creating a new object per call. Negligible.
- `messages.py:249` — fallback `stream_result.model_used or "gemini-2.0-flash"` hard-codes a model name in a string literal. If `model_id` returns the configured value, just drop the fallback and persist the empty string or use `model_id(tier)` directly.
- `MessageMarkdown.tsx:27` — `parseInt(match[1] ?? '0', 10)` — `match[1]` is guaranteed by the regex, the `?? '0'` is dead defensiveness. TS-strict noise.
- `ChatLayout.tsx:65-72` — optimistic user message uses `Date.now()` as id; collides with backend assigned id when persisted message returns (different value). After `refresh`, two user messages appear briefly. Use a negative sentinel and replace on done? Currently no full-refresh is triggered until convo change — likely never duplicates. Low risk.
- `use-conversations.ts:31-42` — refresh always sets `loading=true` on every call (including create→refresh path if you trigger it). Currently only called once on mount, so fine.
- `Header.tsx:185-189` — inline `onClick` calls `router.push('/chat')` but the surrounding code uses Link semantics. Minor; consistent with how the rest of the file handles auth-gated links.

---

## Strengths

1. **Two-step DB commit pattern** (user message commits early, assistant message commits later) — correctly applied in `chat_turn.persist_user_message`. Limits the half-open-transaction window.
2. **`build_citations` index-validation** — silently drops out-of-range `[N]` from hallucinations. Correct.
3. **`X-Accel-Buffering: no` + nginx `proxy_buffering off`** — defense-in-depth. SSE won't stall under either Express-style or nginx proxies.
4. **`ensure_ascii=False` in `sse_event`** — Vietnamese tokens stay readable on the wire (and avoids \uXXXX bloat).
5. **`rehype-sanitize` in `MessageMarkdown`** — blocks `<script>`, `<iframe>`, `javascript:` URLs by default. Confirmed via package defaults. No DOM-XSS vector through markdown.
6. **`AbortController` on FE** — fetch correctly aborts on `cancel()`. (See H2 for backend-side gap.)
7. **`pendingRef`/`fullTextRef` ref-pair** — solves stale-closure on `done` event cleanly. The flushTokens callback is small and correct.
8. **Citation indices unique-in-order** — `extract_used_indices` preserves order of first appearance, which matches what humans expect when scanning `[1]…[2]…[1]…[3]`.
9. **Test coverage of ownership** — 404 for non-owner, 401 unauth, 422 empty content — all three covered.
10. **`accept="application/pdf"`** + JS-side `file.type !== 'application/pdf'` + size guard + server-side magic-bytes (from Phase 03) — three layers, correctly stacked.

---

## Test coverage gaps

- First-token timeout from `generate_stream` (no test; messages.py wraps it but never exercised).
- Empty-token-stream path: `if not accumulated: raise LlmError(...)` at messages.py:238-239 — uncovered.
- `event: citations` snake_case → FE camelCase transform — no FE test exists (no Cypress per report). Without it, C2 went undetected.
- Producer thread leak on client cancellation (H2) — no integration test; backend would need a fake SDK that observes a cancel signal.
- DB pool exhaustion under concurrent streams (H1) — no load test. Recommend a stress test with N=pool_size+5 concurrent streams.
- Markdown XSS attempt smoke test (e.g., `<img onerror=...>` in assistant content) — no test verifying `rehype-sanitize` is active in this app's build.

---

## Unresolved questions

1. **Should `MessageIn` accept `pdf_context_id` from the body**, or is the conversation-attached-PDF model the intended UX (one PDF per conversation, attached at upload time)? C1 fix differs based on the answer.
2. **Should `usePdfUpload.clear()` also DELETE the server-side attachment**? Currently it only clears local React state — DB still has `conv.pdf_context_id` set, so the next message will use the "removed" PDF.
3. **H1 fix preference**: short-lived sessions per DB touch (refactor required) vs. accept connection-per-stream and size pool accordingly?
4. **H2 SDK cancel feasibility**: does google-genai expose `stream.close()` on the sync iterator? If not, the thread leak is intrinsic to the bridge pattern and should be documented.
5. **Q2 from backend report carries over** — should partial-stream LLM errors persist a partial assistant message with an `error` state flag, or stay clean-no-row? Current: clean (good for DB hygiene, awkward UX — partial tokens orphaned in browser).
6. **Q3 from backend report carries over** — `StreamResult.model_used` captured at stream start; SDK may have routed to a different model version. Probably acceptable for v1.
