# Phase 03 — Frontend: Lock-card UI + Entitlement wiring

**Context:** `plan.md` · Phase 01/02 (shape API mới)
**Priority:** High · **Status:** ⬜ Not started

## Overview
Bỏ `IS_VIP=false` hardcode. `/ket-qua` truyền Bearer (nếu đã login) khi gọi report; render theo `locked`
flag từ backend — section khóa hiện **lock-card thật** (không có HTML đầy đủ, chỉ teaser + nút mở khóa).

## Key insights
- Backend giờ trả `tier` + per-section `locked`. FE không tự quyết VIP nữa.
- `NumberCard` đang dựa `isVip` + blur CSS → đổi sang dựa `indicator.locked`/`indicator.content==null`.
- Token: dùng helper auth sẵn có (`lib/user-api.ts` `userFetch`/getJson). Free vẫn xem ẩn danh.

## Requirements
- `getNumerologyReport` đính kèm Authorization nếu có token (qua axiosClient interceptor hoặc userFetch).
- Cập nhật type `NumerologyIndicator`: thêm `locked?: boolean`, `teaser?: string|null`.
- `NumberCard`: nếu `locked` → render teaser + overlay khóa + CTA mở khóa (không blur HTML vì không còn HTML).
- Bỏ prop `isVip` truyền tay khắp các section; thay bằng `locked` từ data. Giữ `isVip` chỉ nếu cần cho layout, nhưng nguồn = API.
- `MainNumberDetail`: chỉ render `content_2..5` khi có (đã sẵn `filter(Boolean)`); thêm lock-card khi các block đó `locked`.

## Architecture
```
page: token? → getNumerologyReport(params, token) → report.tier / per-section locked
sections map indicator → NumberCard
NumberCard:
  locked ? <LockCard teaser onUnlock=/shop?prefill> : <full content>
```

## Related code files
**Modify**
- `Numerology-Landing-Page/src/pages/ket-qua/index.tsx` — bỏ `IS_VIP`; lấy token; dùng `report.tier`; truyền data thẳng.
- `Numerology-Landing-Page/src/modules/result/NumberCard.tsx` — render theo `locked`/teaser, bỏ maskImage blur.
- `Numerology-Landing-Page/src/models/numerology-report.ts` — thêm `locked`, `teaser`, `tier`.
- Các section (`CoreNumbersSection`, `LifePeaksSection`, `ChallengesSection`, `KarmicDebtSection`, `PersonalCycleSection`, `PowerChartSection`, `MainNumberDetail`) — nhận `locked` từ data thay vì `isVip` prop.
- `Numerology-Landing-Page/src/pages/api/numerologyApi.ts` — `getNumerologyReport` nhận token optional.
**Create**
- `Numerology-Landing-Page/src/modules/result/parts/LockCard.tsx` (hoặc inline) — teaser + overlay khóa + CTA.

## Implementation steps
1. Cập nhật types (`locked`,`teaser`,`tier`).
2. `getNumerologyReport(params, token?)` — set header nếu có token.
3. Page: đọc token (helper auth), bỏ `IS_VIP`, dùng `report.tier`. `userInfo.isVip = tier==='paid'`.
4. Tách `LockCard` (teaser + biểu tượng khóa + nút "Mở khóa"). `NumberCard`: `if (indicator.locked) return <LockCard/>`.
5. Gỡ maskImage/blur CSS (không còn HTML để blur).
6. Build FE (`pnpm/npm run build` hoặc `tsc --noEmit`) — fix type errors.

## Todo
- [ ] Types locked/teaser/tier
- [ ] token vào getNumerologyReport
- [ ] page bỏ IS_VIP
- [ ] LockCard + NumberCard refactor
- [ ] gỡ blur CSS
- [ ] compile pass

## Success criteria
- Free: section khóa hiện LockCard với teaser; DevTools network KHÔNG còn HTML luận giải khóa.
- Paid (login + order khớp): section mở hiện full.
- Không lỗi TypeScript.

## Risks
- Token retrieval ở SSR/CSR — đảm bảo chỉ đọc token client-side (useEffect/zustand), tránh hydration mismatch.

## Next
→ Phase 04 hợp nhất CTA + carry-over.
