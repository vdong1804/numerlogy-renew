# Phase 05 Frontend Fixes Report

## Status: completed

---

## C4 — Delete `.prettierrc.json`

**File deleted:** `Numerology-Landing-Page/.prettierrc.json`

No reformatting required. The `.eslintrc` already hardcodes `prettier/prettier: { singleQuote: true, semi: false }` inline — same values the deleted file had. Existing code style unchanged. All P05-touched files were already authored with single quotes / no semis matching the inline ESLint rule.

---

## H2 — Stabilize onQuotaExceeded callback identity

**`src/modules/chat/hooks/use-chat-stream.ts`**

Line 15 — added `useEffect` to import.

Lines 52–57 — added before (old):
```ts
const { onQuotaExceeded } = options
const [streamingText, ...
```
After:
```ts
const { onQuotaExceeded } = options
const onQuotaExceededRef = useRef(onQuotaExceeded)
useEffect(() => { onQuotaExceededRef.current = onQuotaExceeded }, [onQuotaExceeded])
const [streamingText, ...
```
Both `onQuotaExceeded?.()` call sites replaced with `onQuotaExceededRef.current?.()`.

Also added `quota_exceeded_postcommit` handling per backend contract note:
```ts
if (errPayload.code === 'quota_exceeded' || errPayload.code === 'quota_exceeded_postcommit') {
```

**`src/modules/chat/ChatLayout.tsx`**

Line 60 — before: inline arrow `() => setUpsellOpen(true)` passed directly in options object.
After: stable memoised callback:
```ts
const handleQuotaExceeded = useCallback(() => setUpsellOpen(true), [])
// ...
useChatStream(activeConvId, handleMessageComplete, { onQuotaExceeded: handleQuotaExceeded })
```

---

## H3 — Poll quota after bank info shown

**`src/pages/chat/upgrade.tsx`** (lines 73–101) and **`src/modules/chat/parts/UpsellModal.tsx`** (lines 73–101)

Both files: added `useEffect` polling `getQuota()` every 10s when `purchaseInfo !== null`. Stops on `addonRemaining > 0` (success toast) or 5-min timeout (warning toast). Uses `fulfilled` flag pattern to avoid `consistent-return` lint error.

Before: no polling, user must navigate away + back.
After: auto-detects fulfillment and shows `toast.success('Đã kích hoạt gói addon!')`.

Toast library: **sonner** (`toast.success`, `toast.warning`).

---

## M6 — Limit AddonList to 3 packages in UpsellModal

**`src/modules/chat/upgrade/AddonList.tsx`**

Added `limit?: number` prop. Before render: `[...packages].sort((a,b) => a.price - b.price)` then `.slice(0, limit)` when set. Upgrade page unaffected (no `limit` passed).

**`src/modules/chat/parts/UpsellModal.tsx`**

`<AddonList ... limit={3} />`

---

## M7 — Disable all addon CTAs while any purchase in flight

**`src/modules/chat/upgrade/AddonCard.tsx`**

Added `disabled?: boolean` prop. Button: `disabled={loading || disabled}`.

**`src/modules/chat/upgrade/AddonList.tsx`**

Before: `loading={purchasingId === pkg.id}` — only active card disabled.
After:
```tsx
loading={purchasingId === pkg.id}
disabled={purchasingId !== null && purchasingId !== pkg.id}
```
Spinner shows only on in-flight card; all others disabled without spinner.

---

## M8 — Display bankCode in bank info section

**`src/pages/chat/upgrade.tsx`** (line 179) and **`src/modules/chat/parts/UpsellModal.tsx`** (line 157)

Both files: added `InfoRow`/`Row` for `bankCode` between `bankName` and `bankAccountNumber`:
```tsx
<InfoRow label="Mã ngân hàng" value={purchaseInfo.bankCode} mono />
```

---

## M9 — Verify payment content string format

Both `UpsellModal.tsx:139` and `upgrade.tsx:166` already display:
```
`CHATADDON${purchaseInfo.paymentId}`
```
Format matches `CHATADDON123` — no separator, no whitespace. No change needed.

---

## Reformatting note (C4)

No reformatting of existing files needed. The `.eslintrc` inline prettier rule (`singleQuote: true, semi: false`) was already enforcing the same style as the deleted `.prettierrc.json`. All new code written in matching style.

---

## tsc + lint status (last 5 lines)

**tsc:**
```
OK: zero P05 scope TS errors
```

**eslint `src/modules/chat src/pages/chat`:**
```
(no output — zero errors/warnings)
```

---

## Files modified

| File | Change |
|------|--------|
| `Numerology-Landing-Page/.prettierrc.json` | DELETED |
| `src/modules/chat/hooks/use-chat-stream.ts` | H2: ref pattern for onQuotaExceeded; quota_exceeded_postcommit |
| `src/modules/chat/ChatLayout.tsx` | H2: useCallback wrapper for handleQuotaExceeded |
| `src/modules/chat/upgrade/AddonList.tsx` | M6: limit prop + sort; M7: disabled prop to AddonCard |
| `src/modules/chat/upgrade/AddonCard.tsx` | M7: disabled prop on Button |
| `src/modules/chat/parts/UpsellModal.tsx` | H3: quota polling; M6: limit=3; M8: bankCode row |
| `src/pages/chat/upgrade.tsx` | H3: quota polling; M8: bankCode row |

---

## Unresolved

None.
