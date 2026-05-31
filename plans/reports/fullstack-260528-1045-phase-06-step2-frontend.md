# Phase 06 Step 2 Frontend — Rate-Limit 429 Handling

## Files Created / Modified

| File | Action | LOC |
|------|--------|-----|
| `src/modules/chat/hooks/use-rate-limit-countdown.ts` | created | 75 |
| `src/modules/chat/hooks/use-chat-stream.ts` | modified | +45 |
| `src/modules/chat/ChatLayout.tsx` | modified | +20 |
| `src/modules/chat/parts/MessageInput.tsx` | modified | +12 |

## Tasks Completed

- [x] New hook `useRateLimitCountdown` — trigger/clear, 1s tick, unmount cleanup
- [x] `UseChatStreamOptions.onRateLimited` added + ref-stabilised (mirrors onQuotaExceededRef pattern)
- [x] SSE `rate_limited` branch in `handleFrame`
- [x] HTTP 429 branch in `!res.ok` block (prefer body `retry_after`, fallback to `Retry-After` header)
- [x] `handleRateLimited` callback in ChatLayout wired to `useChatStream`
- [x] `rateLimit.clear()` called after successful send
- [x] `rateLimitActive` + `rateLimitSecondsLeft` props threaded to `MessageInput`
- [x] Send button + Enter key gated on `rateLimitActive`
- [x] Countdown hint rendered above input when active
- [x] Distinct toast variants: `bucket_empty` → warning 3s, `daily_cap` → error 8s

## SSE Error Branch (exact snippet added)

```ts
if (errPayload.code === 'rate_limited') {
  const retryAfter =
    typeof errPayload.retry_after === 'number' ? errPayload.retry_after : 0
  const reason = (errPayload.reason === 'daily_cap'
    ? 'daily_cap'
    : 'bucket_empty') as 'bucket_empty' | 'daily_cap'
  onRateLimitedRef.current?.(retryAfter, reason)
  setError(null)
  return
}
```

## Toast Lib + Reason Variants

- Lib: `sonner` (already used in `UpsellModal.tsx` and `upgrade.tsx`)
- `bucket_empty`: `toast.warning(...)` duration 3000ms
- `daily_cap`: `toast.error(...)` duration 8000ms

## Reuse Decisions

- Ref stabilisation pattern copied directly from `onQuotaExceededRef` — no new pattern introduced
- Hint `<p>` styling reuses existing quota hint classes (`mb-1.5 text-xs ... text-center`) — swapped `text-destructive/80` → `text-warning/80` for visual distinction
- `sonner` already a dependency — no new package

## tsc + lint (last 5 lines)

```
tsc: OK: zero chat-related TS errors
lint (after --fix): (no output — zero errors/warnings)
```

## Unresolved

- `text-warning/80` Tailwind token: if project palette doesn't define `warning`, it silently renders transparent. If so, swap to `text-amber-500/80` or `text-yellow-600`. Not blocking — functional behaviour is unaffected.
- SSE `rate_limited` spec doesn't include `reason` field — backend agent should confirm whether to add it. Default `bucket_empty` used; toast message from `handleRateLimited` is always correct since ChatLayout computes the copy from `reason`.
