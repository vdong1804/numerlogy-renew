# Phase 04 — Streaming + Next.js /chat UI

## Context Links
- Depends on: P2 (LLM service) + P3 (PDF upload UI hook)
- Brainstorm: §4.3 streaming flow, §4.5 UI placement

## Overview
- **Priority:** High
- **Status:** complete (2026-05-27)
- **Duration:** 2 weeks
- **Description:** Add SSE streaming endpoint to backend, build Next.js `/chat` page (conversation sidebar, message stream rendering, citation panel, PDF upload), use existing JWT auth context.

## Key Insights
- Streaming = SSE (Server-Sent Events) over fetch + ReadableStream — simpler than WebSocket, native FastAPI support via `StreamingResponse`.
- Citation panel slides in on hover/click of `[N]` markers — show chunk content + source.
- Markdown rendering: `react-markdown` + `remark-gfm`; sanitize via `rehype-sanitize`.
- Nginx must `proxy_buffering off` + `proxy_read_timeout 300s` for SSE.
- Reuse existing `useAuth` hook (JWT in localStorage) from `src/hooks/` or `src/store/`.

## Requirements

### Functional
- POST `/api/chat/conversations/{id}/messages/stream` returns `text/event-stream`.
- Events: `delta` (token chunks), `citations` (final payload), `done` (end), `error`.
- Next.js page `/chat` with:
  - Left sidebar: conversation list (collapsed on mobile)
  - Center: message thread with auto-scroll
  - Bottom: input box + PDF upload button + send button
  - Right (paid users): citation drawer
- New conversation button + delete confirmation
- Markdown rendering with code blocks, lists, bold/italic
- Mobile responsive

### Non-Functional
- First token latency <1.2s.
- Smooth scroll, no jank on rapid token arrival.
- Reconnect on network drop (within same SSE stream).
- Accessibility: keyboard nav, ARIA labels.

## Architecture

### Backend additions
```
app/routers/chat/messages.py            # +POST /stream endpoint
app/services/chat/sse_formatter.py      # format SSE events
```

### Frontend new files
```
Numerology-Landing-Page/src/
├── pages/chat.tsx                                  # entry page (≤80 LOC)
├── modules/chat/
│   ├── ChatLayout.tsx                              # layout shell
│   ├── ConversationSidebar.tsx                     # list + new/delete
│   ├── MessageThread.tsx                           # render messages
│   ├── MessageInput.tsx                            # textarea + send + upload
│   ├── CitationDrawer.tsx                          # source viewer
│   ├── PdfUploadButton.tsx                         # multipart upload
│   ├── MessageMarkdown.tsx                         # md renderer w/ citation refs
│   ├── hooks/
│   │   ├── useConversations.ts                     # list/create/delete
│   │   ├── useMessages.ts                          # fetch history
│   │   ├── useChatStream.ts                        # SSE consumer
│   │   └── usePdfUpload.ts                         # upload + attach
│   └── api/
│       └── chatApi.ts                              # axios wrappers
├── models/Chat.ts                                  # TypeScript types
└── styles/chat.module.css
```

## SSE Event Format

```
event: delta
data: {"token":"Số "}

event: delta
data: {"token":"đường "}

event: citations
data: {"citations":[{"index":1,"chunk_id":42,...}]}

event: done
data: {"message_id":123,"input_tokens":1200,"output_tokens":300,"model_used":"gemini-2.0-flash"}

event: error
data: {"code":"quota_exceeded","message":"..."}
```

## Related Code Files

### Create (backend)
- `app/services/chat/sse_formatter.py` (≤60 LOC)
- `tests/routers/chat/test_stream_endpoint.py`

### Modify (backend)
- `app/routers/chat/messages.py` — add streaming endpoint
- `app/services/chat/llm_service.py` — implement `generate(..., stream=True)` returning AsyncIterator

### Create (frontend) — all listed above

### Modify (frontend)
- `next.config.js` — proxy rewrite for `/api/chat/*` if needed
- `src/pages/_app.tsx` — verify auth context wraps `/chat`
- Navigation (header) — add Chat link for logged-in users

### Modify (infra)
- `deploy/nginx.conf` — `location /api/chat/ { proxy_buffering off; proxy_read_timeout 300s; }`

## Implementation Steps

### Backend
1. **SSE formatter helper**
   ```python
   def sse_event(event: str, data: dict) -> bytes:
       return f"event: {event}\ndata: {json.dumps(data)}\n\n".encode()
   ```

2. **Streaming endpoint**
   ```python
   @router.post("/{conv_id}/messages/stream")
   async def stream_message(conv_id: int, body: MessageIn, user=Depends(get_current_user)):
       async def event_gen():
           # save user msg
           # retrieve KB + PDF chunks
           # build prompt
           async for token in llm_service.generate(..., stream=True):
               yield sse_event("delta", {"token": token})
           yield sse_event("citations", {"citations": [...]})
           # save assistant msg
           yield sse_event("done", {...})
       return StreamingResponse(event_gen(), media_type="text/event-stream",
                                headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})
   ```

3. **LlmService stream impl** — `model.generate_content_async(..., stream=True)` yields parts.

### Frontend
4. **TypeScript types** (`models/Chat.ts`)
   ```ts
   export interface Conversation { id: number; title: string; createdAt: string; pdfContextId?: number }
   export interface Message { id: number; role: 'user'|'assistant'; content: string; citations: Citation[] }
   export interface Citation { index: number; chunkId: number; sourceType: string; title?: string; score: number }
   ```

5. **API wrappers** (`chatApi.ts`) — axios with JWT interceptor (reuse existing).

6. **Hooks**
   - `useConversations`: React Query for list + mutations.
   - `useMessages(convId)`: React Query infinite scroll history.
   - `useChatStream(convId)`:
     ```ts
     const send = async (content: string) => {
       const res = await fetch(url, { method: 'POST', headers: {...}, body });
       const reader = res.body!.getReader();
       const decoder = new TextDecoder();
       // parse SSE events, dispatch tokens/citations
     };
     ```
   - `usePdfUpload`: FormData multipart, return `pdfContextId`.

7. **Components**
   - `ChatLayout`: 3-column responsive grid (sidebar + main + drawer).
   - `ConversationSidebar`: list + "+ New" button + delete confirm.
   - `MessageThread`: virtualized list (`react-window`) for long history; auto-scroll on new tokens; render markdown via `MessageMarkdown`.
   - `MessageMarkdown`: `react-markdown` + custom renderer for `[N]` → clickable span dispatching `setActiveCitation`.
   - `MessageInput`: textarea (auto-expand), `Enter` to send, `Shift+Enter` newline, drag-drop PDF zone.
   - `CitationDrawer`: side panel showing chunk content + source link, closeable.
   - `PdfUploadButton`: shows attached PDF filename + remove button.

8. **Loading + error states**
   - Skeleton while history loads.
   - Toast on stream error.
   - Quota exceeded → modal with upsell CTA (Phase 05 wires payment).

9. **Header nav**
   - Add `Chat` link visible only to authenticated users.

### Infra
10. **Nginx**
    - Add SSE-friendly config block. Test with `curl -N`.

## Todo List

- [x] Implement backend streaming endpoint + SSE formatter
- [x] Extend LlmService for async streaming
- [x] Test SSE flow with curl: `curl -N -H "Authorization: Bearer ..." ...`
- [x] Update nginx config + reload on staging
- [x] Create Next.js `pages/chat.tsx` + ChatLayout
- [x] Build ConversationSidebar with CRUD
- [x] Build MessageThread with virtualized list + auto-scroll
- [x] Build MessageMarkdown with citation refs
- [x] Build MessageInput with PDF upload zone
- [x] Build CitationDrawer
- [x] Implement chat API wrappers + JWT interceptor
- [x] Implement React Query hooks (conversations, messages)
- [x] Implement useChatStream SSE consumer
- [x] Implement usePdfUpload multipart
- [x] Add Chat link to header for logged-in users
- [ ] Mobile responsive QA (320px, 768px, 1280px) — deferred to Phase 08
- [ ] Accessibility audit (aria-labels, keyboard nav) — deferred to Phase 08
- [ ] E2E test with Cypress: login → send msg → verify streaming + citation — deferred to Phase 08
- [ ] Lighthouse score ≥85 performance — deferred to Phase 08

## Completion Notes

**Completion Date:** 2026-05-27

**Actual Files Created (Backend)**
- `app/routers/chat/messages.py` — POST `/api/chat/conversations/{id}/messages/stream` streaming endpoint (185 LOC)
- `app/services/chat/sse_formatter.py` — SSE event formatter helper
- `app/services/chat/_stream_generator.py` — extracted streaming generator logic (120 LOC)
- `app/services/chat/chat_turn.py` — shared `persist_no_info_assistant` helper
- `tests/routers/chat/test_stream_endpoint.py` — comprehensive SSE streaming tests (40/40 pass)

**Actual Files Created (Frontend)**
- `src/pages/chat.tsx` — main chat page entry
- `src/modules/chat/ChatLayout.tsx` — 3-column responsive layout
- `src/modules/chat/parts/ConversationSidebar.tsx` — sidebar with CRUD
- `src/modules/chat/parts/MessageThread.tsx` — message render + auto-scroll with "new messages" pill
- `src/modules/chat/parts/MessageInput.tsx` — textarea + send + PDF upload zone
- `src/modules/chat/parts/CitationDrawer.tsx` — side panel source viewer
- `src/modules/chat/MessageMarkdown.tsx` — markdown renderer with `[N]` citation refs
- `src/modules/chat/hooks/use-conversations.ts` — React Query list/create/delete
- `src/modules/chat/hooks/use-messages.ts` — history fetch
- `src/modules/chat/hooks/use-chat-stream.ts` — SSE consumer with event parsing
- `src/modules/chat/hooks/use-pdf-upload.ts` — multipart PDF upload + attachment
- `src/modules/chat/api/chat-api.ts` — axios wrappers + citation mapper `toCitation()`
- `src/models/Chat.ts` — TypeScript interfaces
- `src/styles/chat.module.css` — responsive styling

**Infra Changes**
- `deploy/nginx.conf` — regex location for `/api/chat/conversations/{id}/messages/stream` with `proxy_buffering off`, `gzip off`, 300s timeouts

**Key Deviations from Plan**
1. PDF upload reuses existing conversation-scoped endpoint (`POST /api/chat/conversations/{id}/documents`) instead of separate `/pdf-uploads` endpoint — simpler, consistent with Phase 03 design
2. Extracted `_stream_generator.py` (120 LOC) + `chat_turn.py` helpers (DRY principle) to separate modules
3. `MessageIn` contract extended: `pdf_context_id` field in body (optional), allows attaching PDF to same message request
4. Frontend: `_streamingCitations` state removed; citation parsing deferred to SSE `citations` event for cleaner SSE contract alignment
5. MessageThread: Added `isNearBottom` guard + "Có tin nhắn mới" (new messages) pill to prevent auto-scroll interruption during user scroll-up

**Tests & Validation**
- Backend: 40/40 tests pass (7 streaming happy-path, error handling, auth, PDF context)
- Frontend: Zero TS/lint errors in chat scope
- Nginx: SSE directives correctly applied + tested with curl
- Wire contract: Citation fields exact match (snake_case wire, camelCase models)
- Code review: 2 critical + 6 high + 8 medium issues resolved; 2 follow-up contract fixes applied

**Validation Report**
See `tester-260527-0900-phase-04-validation.md` for full test suite + type-check results.

## Success Criteria
- Tokens render incrementally without flicker. ✓
- Citation [N] click opens drawer with correct source. ✓
- PDF upload attaches and next message references PDF. ✓
- Mobile responsive implementation deferred to Phase 08. ⏳
- Cypress E2E deferred to Phase 08. ⏳

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Nginx buffers SSE → no streaming | `proxy_buffering off` + `X-Accel-Buffering: no` header |
| Token rendering causes re-render storm | Append to ref + batch via `useTransition`; render every 50ms |
| Citation parsing in markdown breaks links | Custom renderer; test with `[1]` inside lists, code blocks |
| Mobile keyboard pushes input out of view | `position: sticky` + `100dvh` instead of `100vh` |
| JWT expires mid-stream | Refresh token before fetch; on 401 mid-stream, abort + relogin prompt |
| Network drop loses partial stream | Show "Connection lost. Resend?" with content drafted preserved |

## Security Considerations
- Sanitize markdown with `rehype-sanitize` (block `<script>`, `<iframe>`).
- Citations from server only — never trust frontend-supplied citation chunk_ids.
- PDF upload size enforced both client (UI feedback) + server (hard reject).
- CORS: ensure `/chat` origin matches existing config.

## Next Steps / Dependencies
- **Unlocks:** Phase 05 quota integration plugs into UI (upsell modal).
- **Required for:** Public launch.
- **Parallel-safe with:** Phase 05 backend work.
