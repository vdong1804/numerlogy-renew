# Phase-04 FE↔BE Contract Fixes Report

**Date:** 2026-05-27
**Status:** Completed

---

## Mismatch 1 — Response envelope unwrap

**Before** (`listConversations`):
```ts
const raw = await getJson<ConversationRaw[]>('/api/chat/conversations')
// raw was actually { data: [...], total, limit, offset } — wrong type
```

**After:**
```ts
async function getData<T>(path: string): Promise<T> {
  const env = await getJson<{ data: T }>(path)
  return env.data
}
const raw = await getData<ConversationRaw[]>('/api/chat/conversations')
```

Same pattern applied to: `listMessages`, `createConversation` (POST), `uploadPdf` (POST).
`deleteConversation` → 204 no body, no change needed.

---

## Mismatch 2 — PDF upload endpoint + conversationId requirement

**Before:**
```ts
export async function uploadPdf(file: File): Promise<PdfUploadResult> {
  const res = await userFetch('/api/chat/pdf-uploads', { method: 'POST', body: form })
```

**After:**
```ts
export async function uploadPdf(conversationId: number, file: File): Promise<PdfUploadResult> {
  const res = await userFetch(`/api/chat/conversations/${conversationId}/upload-pdf`, ...)
```

`usePdfUpload` now accepts `conversationId: number | null`; early-returns with error message when null.
`ChatLayout` passes `activeConvId` → `usePdfUpload(activeConvId)`.
`PdfUploadButton` gains `hasConversation?: boolean` prop (defaults true); shows tooltip "Vui lòng chọn hoặc tạo cuộc trò chuyện trước" and disables when false.

---

## Mismatch 3 — PdfUploadResult shape

**Before:**
```ts
export interface PdfUploadResult { pdf_context_id: number; filename: string }
// filename doesn't exist in backend response
```

**After:**
```ts
interface PdfUploadRaw { pdf_context_id, matched, matched_report_id, page_count, chunks_created, expires_at }
export interface PdfUploadResult { pdfContextId, matched, matchedReportId, pageCount, chunksCreated, expiresAt }
// toPdfUploadResult() maps snake→camel (consistent with toConversation/toMessage)
```

`filename` in UI pill now sourced from `file.name` (local File object) in `usePdfUpload`:
```ts
setAttachment({ pdfContextId: result.pdfContextId, filename: file.name })
```

---

## Files Modified

| File | Delta |
|------|-------|
| `src/modules/chat/api/chat-api.ts` | +54 / -20 (added getData, toPdfUploadResult, PdfUploadRaw, fixed all 4 call sites) |
| `src/modules/chat/hooks/use-pdf-upload.ts` | +20 / -15 (conversationId param, file.name source) |
| `src/modules/chat/parts/PdfUploadButton.tsx` | +10 / -6 (hasConversation prop, isDisabled, tooltip) |
| `src/modules/chat/ChatLayout.tsx` | +1 / -1 (pass activeConvId to usePdfUpload) |

---

## TypeScript / Lint

```
tsc --noEmit → 0 errors in src/modules/chat/**
eslint --fix  → 1 auto-fix (redundant parens), 0 errors
```

Pre-existing errors in `analytics.tsx`, `turnstile-widget.tsx`, `cookie-consent.tsx`, `BankInfo.tsx` — untouched, out of scope.

---

## New TODOs Surfaced

- `PdfUploadButton.hasConversation` defaults to `true` — currently only used when explicitly passed. `ChatLayout` gates the entire input area on `activeConvId != null`, so the prop isn't exercised in practice. Future: thread it through `MessageInput` if the gate logic changes.
- `PdfUploadResult.matchedReportId` / `chunksCreated` not yet consumed in UI — available if needed for a "matched report" CTA.

---

## Unresolved Questions

- None.
