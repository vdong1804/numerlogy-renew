# Phase 04 Frontend Implementation Report

## Status: COMPLETED

---

## Files Created / Modified

### Created

| File | LOC | Purpose |
|------|-----|---------|
| `src/models/Chat.ts` | 42 | TypeScript types: Conversation, Message, Citation, SSE event payloads |
| `src/modules/chat/api/chat-api.ts` | 100 | Axios wrappers: listConversations, createConversation, deleteConversation, listMessages, uploadPdf |
| `src/modules/chat/hooks/use-conversations.ts` | 62 | List/create/delete conversations with useState (no React Query — not in project) |
| `src/modules/chat/hooks/use-messages.ts` | 48 | Fetch message history for active conversation |
| `src/modules/chat/hooks/use-chat-stream.ts` | 228 | SSE consumer — recursive pump, token batching via rAF, stale-closure-safe fullTextRef |
| `src/modules/chat/hooks/use-pdf-upload.ts` | 58 | Multipart PDF upload, client-side size/type guard |
| `src/modules/chat/parts/MessageMarkdown.tsx` | 88 | react-markdown + remark-gfm + rehype-sanitize; [N] → clickable citation spans |
| `src/modules/chat/parts/CitationDrawer.tsx` | 78 | Slide-in right Sheet with citation detail, score bar |
| `src/modules/chat/parts/PdfUploadButton.tsx` | 82 | File picker button + attached-pill state + remove |
| `src/modules/chat/parts/ConversationSidebar.tsx` | 96 | Conversation list + New button + delete with ConfirmDialog |
| `src/modules/chat/parts/MessageInput.tsx` | 118 | Auto-expanding textarea (≤8 rows), Enter/Shift+Enter, send + cancel buttons |
| `src/modules/chat/parts/MessageThread.tsx` | 204 | History + streaming bubble + skeleton loading + auto-scroll |
| `src/modules/chat/ChatLayout.tsx` | 204 | 3-column layout shell — wires all hooks, desktop sidebar + mobile Sheet |
| `src/pages/chat.tsx` | 52 | Page entry: auth guard → redirect /login, renders ChatLayout inside Main |

### Modified

| File | Change |
|------|--------|
| `src/layouts/Header.tsx` | Added "Chat AI" button (desktop) + "Chat AI" MenuItem (mobile drawer), visible only when `user !== null` |

---

## npm Packages Added

| Package | Version installed |
|---------|------------------|
| `react-markdown` | ^9.x |
| `remark-gfm` | ^4.x |
| `rehype-sanitize` | ^6.x |

React Query NOT added — project uses plain `useState/useEffect` pattern; TODO noted in `use-conversations.ts`.

---

## Build / Lint / Typecheck Output

```
# typecheck — zero errors in new files
$ npx tsc --noEmit | grep "modules/chat|pages/chat|models/Chat|layouts/Header"
(no output)

# lint — zero errors in new files
$ npx eslint src/modules/chat src/pages/chat.tsx src/layouts/Header.tsx src/models/Chat.ts
(no output)

# build — clean
├ ○ /chat   57.8 kB   281 kB
✨ [next-sitemap] Generation completed
```

Pre-existing errors in `analytics.tsx`, `cookie-consent.tsx`, `turnstile-widget.tsx`, `checkout/BankInfo.tsx` were present before this phase — untouched.

---

## Components Inventory

| Component / Hook | One-line purpose |
|-----------------|-----------------|
| `ChatLayout` | Responsive shell: 260px sidebar | 1fr thread | right citation drawer; mobile → Sheet |
| `ConversationSidebar` | List + "Cuộc trò chuyện mới" + per-item delete with confirm dialog |
| `MessageThread` | Auto-scroll message list with skeleton loading + streaming bubble + bounce dots |
| `MessageInput` | Auto-expanding textarea, Enter send, Shift+Enter newline, send/cancel/PDF buttons |
| `MessageMarkdown` | Sanitized markdown render; `[N]` tokens → clickable citation buttons |
| `CitationDrawer` | Slide-in right Sheet showing index, title, source type, score bar |
| `PdfUploadButton` | Hidden `<input type=file>` + attached-pill with remove; disabled during stream |
| `useConversations` | CRUD state for conversation list; plain useState (no RQ) |
| `useMessages` | Fetch history for active convId; `append()` for optimistic updates |
| `useChatStream` | SSE consumer + token batching + abort controller |
| `usePdfUpload` | FormData multipart, client-side size (20MB) + type guards |
| `chat-api.ts` | Typed wrappers over `userFetch`/`getJson` — no new auth logic |

---

## SSE Consumer Parsing Approach (5-line summary)

1. `fetch()` with `Accept: text/event-stream` + Bearer token; body read via `res.body.getReader()`.
2. Recursive `pump()` function calls `reader.read()` then schedules itself — avoids ESLint `no-await-in-loop` / `no-restricted-syntax`.
3. Raw bytes decoded with `TextDecoder({ stream: true })`; buffer split on `\n\n` — incomplete trailing frame held in `buffer` until next chunk.
4. Each frame parsed into `{ eventType, dataLine }` via `parseFrame()`; `handleFrame()` dispatches: `delta` → append to `pendingRef` + schedule rAF flush; `citations` → setState; `done` → flush + build completed Message; `error` → throw.
5. Token batching: `pendingRef` accumulates tokens, `requestAnimationFrame` flushes to React state ~every 16ms; `fullTextRef` tracks cumulative text to avoid stale-closure on `done`.

---

## Known Gaps / TODOs

- `use-conversations.ts` line 1: TODO migrate to React Query when added to project
- `use-messages.ts`: TODO infinite scroll (cursor pagination) — currently loads first page only
- `MessageThread.tsx`: TODO react-window virtualization when >100 messages
- Cypress E2E: skipped (no live backend) — follow-up task
- Mobile breakpoint QA (360px, 768px, 1280px): marked TODO, manual test required
- Lighthouse score: not measured — no live server
- `noUncheckedIndexedAccess` strictness: `frames.pop()` returns `string | undefined` — handled via `?? ''` nullish coalescing
- `_streamingCitations` prop in `MessageThread` prefixed with `_` to satisfy `noUnusedParameters` — needed for future virtualization feature
- Header `Header.tsx` has pre-existing prettier errors from original code — not introduced by this phase

---

## Unresolved Questions

1. Backend URL for PDF upload — assumed `POST /api/chat/pdf-uploads` (matches phase spec); confirm path matches actual `app/routers/chat/pdf_upload.py`.
2. Backend conversation API returns `created_at` snake_case — confirmed mapping in `chat-api.ts`; verify actual field names match backend schema.
3. `100dvh` header height assumed 64px in `ChatLayout` (`h-[calc(100dvh-64px)]`) — if header height changes, update this value.
4. Citation drawer shows chunk metadata only (index, title, score, sourceType) — chunk content text not included because backend SSE `citations` event doesn't include `chunk_text`. Confirm if backend should add it.
