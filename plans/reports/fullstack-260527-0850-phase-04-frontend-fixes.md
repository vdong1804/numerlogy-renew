# Phase 04 Frontend Fixes Report

## Status: completed

---

## Files Modified

| File | Changes |
|------|---------|
| `src/models/Chat.ts` | Added `documentId`, `sourceRef` to `Citation` |
| `src/modules/chat/api/chat-api.ts` | Added `CitationRaw`, `toCitation()`, `clearPdfContext()`, updated `MessageRaw.citations` type + `toMessage()` |
| `src/modules/chat/hooks/use-chat-stream.ts` | Import `CitationRaw`/`toCitation`, map SSE citations, replace recursive `pump()` with while-loop |
| `src/modules/chat/hooks/use-pdf-upload.ts` | `clear()` → async, calls `clearPdfContext()` with optimistic revert |
| `src/modules/chat/parts/PdfUploadButton.tsx` | `onRemove` → `Promise<void>`, added `removing` state + spinner |
| `src/modules/chat/parts/MessageInput.tsx` | `onPdfRemove` type → `() => Promise<void>` |
| `src/modules/chat/parts/MessageThread.tsx` | Removed `streamingCitations` prop, added scroll container ref + `isNearBottom` state + "new messages" pill |
| `src/modules/chat/ChatLayout.tsx` | Removed `streamingCitations` prop pass, optimistic id → negative sentinel counter |
| `src/modules/chat/parts/MessageMarkdown.tsx` | `match[1] ?? '0'` → `match[1]!` (non-null assertion) |

---

## Fix Details

### Fix #1 — C2: Citation type + toCitation mapper

`src/models/Chat.ts:13`
```ts
// before
  chunkId: number
  sourceType: string
// after
  chunkId: number
  documentId: number
  sourceType: string
  sourceRef: string
```

`src/modules/chat/api/chat-api.ts` — new exports added before `MessageRaw`:
- `CitationRaw` interface (snake_case wire shape)
- `toCitation(r: CitationRaw): Citation` mapper
- `MessageRaw.citations` updated to `CitationRaw[]`; `toMessage()` uses `toCitation`

`src/modules/chat/hooks/use-chat-stream.ts:153`
```ts
// before
const { citations } = parsed as SseCitationsEvent
finalCitations = citations
setStreamingCitations(citations)
// after
const { citations } = parsed as { citations: CitationRaw[] }
const mapped = citations.map(toCitation)
finalCitations = mapped
setStreamingCitations(mapped)
```

### Fix #2 — C1 frontend: async clear + clearPdfContext

`src/modules/chat/api/chat-api.ts` — added `clearPdfContext(conversationId)` calling `PATCH /api/chat/conversations/{id}/pdf-context` with `{ pdf_context_id: null }`.

`src/modules/chat/hooks/use-pdf-upload.ts:73`
```ts
// before: sync, local-only
const clear = useCallback(() => { setAttachment(null); setError(null) }, [])
// after: async, optimistic with revert on error
const clear = useCallback(async () => {
  if (conversationId == null) { setAttachment(null); setError(null); return }
  const previous = attachment
  setAttachment(null); setError(null)
  try { await clearPdfContext(conversationId) }
  catch (err) { setAttachment(previous); setError(...) }
}, [conversationId, attachment])
```

`PdfUploadButton.tsx` + `MessageInput.tsx` — `onRemove`/`onPdfRemove` typed as `() => Promise<void>`; button shows `Loader2` spinner while `removing` state is true.

### Fix #3 — H4: near-bottom auto-scroll guard

`src/modules/chat/parts/MessageThread.tsx`
- Added `scrollContainerRef` + `isNearBottom` state (default `true`)
- `handleScroll`: `nearBottom = scrollHeight - scrollTop - clientHeight < 80`
- `useEffect` scroll only fires when `isNearBottom`
- Added outer wrapper `<div className="flex-1 relative overflow-hidden">` for pill positioning
- "↓ Có tin nhắn mới" pill: visible when `isStreaming && !isNearBottom`

### Fix #4 — H5: while-loop replaces recursive pump()

`src/modules/chat/hooks/use-chat-stream.ts:185`
```ts
// before: recursive pump() function
// after:
// eslint-disable-next-line no-constant-condition
while (true) {
  // eslint-disable-next-line no-await-in-loop
  const { done, value } = await reader.read()
  if (done) break
  ...
}
```

### Fix #5 — M6: remove _streamingCitations

`MessageThreadProps` — removed `streamingCitations: Citation[]`; destructure no longer has `_streamingCitations`.
`ChatLayout.tsx` — removed `streamingCitations={streamingCitations}` prop (retained in `handleCitationClick` logic).

### Fix #6 — L: optimistic id negative sentinel

`src/modules/chat/ChatLayout.tsx`
```ts
// before: id: Date.now()
// after:
const optimisticIdRef = useRef(-1)
// in handleSend:
optimisticIdRef.current -= 1
id: optimisticIdRef.current  // starts at -2, -3, ...
```

### Fix #7 — L: MessageMarkdown dead defensiveness

`src/modules/chat/parts/MessageMarkdown.tsx:27`
```ts
// before: parseInt(match[1] ?? '0', 10)
// after:  parseInt(match[1]!, 10)  — regex guarantees capture group
```
Note: TS types `RegExpMatchArray[n]` as `string | undefined`; `??` replaced with non-null assertion `!` to satisfy both tsc strictness and eliminate dead code.

---

## Validation

### tsc --noEmit
Zero errors in `src/modules/chat/**` and `src/models/Chat.ts`.
Pre-existing errors only in unowned files:
```
src/components/analytics.tsx(60,3): error TS2532
src/components/cookie-consent.tsx(9,3): error TS6133
src/components/turnstile-widget.tsx(37,7): error TS2352
src/modules/checkout/BankInfo.tsx(18,17): error TS6133
src/modules/checkout/parts/TextCopy.tsx(15,10): error TS6133
```

### ESLint
```
npx eslint src/modules/chat src/models/Chat.ts → (no output, exit 0)
```
Zero errors, zero warnings in owned files.

---

## Deviations

- Fix #7: used `match[1]!` (non-null assertion) instead of removing `?? '0'` entirely, because tsc strict treats `RegExpMatchArray[1]` as `string | undefined`. Semantically equivalent to review intent.
- Fix #2 body contract: `pdf_context_id` is omitted from stream body when undefined (no clear-on-send); explicit clear only via PATCH as specified.

---

## Unresolved

None introduced by these fixes. Pre-existing from code review:
- H1 (DB pool leak during streams) — backend agent scope
- H2 (producer thread not cancelled on abort) — backend agent scope
- M1 (multi-line data: frame parsing) — accepted risk, documented in review
