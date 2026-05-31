# Phase 06 Frontend Fixes Report

## Files Modified

- `src/modules/chat/hooks/use-rate-limit-countdown.ts` — 3 lines changed
- `src/modules/chat/hooks/use-chat-stream.ts` — 14 lines deleted

---

## Fix H8 — useRateLimitCountdown interval cleanup

**Was a real bug? Partially.** Not data-corrupting, but the redundant-tick described in review was real:
- When `next <= 0`, the functional updater returned `active: false` but did NOT clear the interval.
- The interval was cleared 1 tick later via the `useEffect` watching `state.active`.
- During that gap, one extra `setInterval` tick fires, calling `setState` again with `secondsLeft = 0 - 1 = -1`, which the guard catches and returns `active: false, secondsLeft: 0` — React bails (same shape). Wasteful, not broken.

**Fix applied** — clear interval inside the functional updater when `next <= 0`:

```
Before (line 51-54):
  if (next <= 0) {
    // Will be cleaned up in effect below
    return { active: false, secondsLeft: 0, reason: null }
  }

After:
  if (next <= 0) {
    // Clear interval immediately inside the updater to avoid a
    // redundant tick between setState and the effect cleanup.
    stopInterval()
    return { active: false, secondsLeft: 0, reason: null }
  }
```

The `useEffect` fallback (line ~63) is kept for the `clear()` path where `active` is set to false externally. Comment updated to reflect this.

File: `src/modules/chat/hooks/use-rate-limit-countdown.ts` lines 51-67

---

## Fix C6/Unresolved#6 — Remove dead SSE `rate_limited` branch

**Deleted** the 14-line block handling `errPayload.code === 'rate_limited'` inside `handleFrame`.

```
Before (lines 239-252 in use-chat-stream.ts):
  const errPayload = parsed as SseErrorEvent & {
    retry_after?: number
    reason?: string
  }
  if (errPayload.code === 'rate_limited') {
    ... onRateLimitedRef.current?.(retryAfter, reason)
    setError(null)
    return
  }
  if (errPayload.code === 'quota_exceeded' ...

After:
  const errPayload = parsed as SseErrorEvent
  if (errPayload.code === 'quota_exceeded' ...
```

REST 429 path (`!res.ok` + `Retry-After` header parsing, lines 156-178) is untouched and remains the active path.

File: `src/modules/chat/hooks/use-chat-stream.ts` lines 234-252

---

## Vietnamese Copy Check

- **Toast rate-limit** (ChatLayout.tsx:78): `Bạn gửi tin nhắn quá nhanh. Vui lòng đợi ${retryAfter} giây.` — matches backend message verbatim. No change.
- **Input hint** (MessageInput.tsx:113): `Chờ {rateLimitSecondsLeft}s trước khi gửi tin nhắn mới` — consistent voice. Spec example had `⏳` emoji prefix; omitted here per existing code style (no emojis in UI hints). No change needed.
- **Daily cap toast** (ChatLayout.tsx:71): `Bạn đã đạt giới hạn tin nhắn hôm nay. Thử lại vào ngày mai.` — consistent. No change.

---

## Validation

**tsc (`--noEmit`):** Zero errors in `modules/chat` or `hooks/use-rate-limit*`. Pre-existing errors in `analytics.tsx`, `turnstile-widget.tsx`, `checkout/` — unrelated to this phase.

**eslint (`src/modules/chat`):**
```
(no output — zero errors, zero warnings)
```

---

## Unresolved

None from frontend scope. Backend items (C1, C2, C3, H1, H7 chunking) are handled by the other agent.
