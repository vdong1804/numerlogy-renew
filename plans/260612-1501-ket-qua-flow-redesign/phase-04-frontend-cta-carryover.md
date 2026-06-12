# Phase 04 — Frontend: Unified CTA + Carry-over + Sticky Purchase Bar

**Context:** `plan.md` · Phase 03
**Priority:** Med · **Status:** ⬜ Not started

## Overview
Hợp nhất 3 điểm upsell rời rạc (banner, mỗi card, box PDF) thành: lock-card hint (Phase 03) + **một sticky
purchase bar** hiển thị gói gợi ý + giá. Mọi CTA deep-link `/shop/[slug]?prefill` **mang theo customerInfo**
để `/shop/[slug]` không bắt nhập lại (findings #4, #6, #7).

## Key insights
- `/shop/[slug]` report-type có form name/birth_day/phone/gender — cần prefill từ query/localStorage.
- Gói gợi ý: chọn product `type` phù hợp (report của số chủ đạo) — lấy từ `listProducts('report')` rồi pick theo quy ước (vd sort_order/sku), hoặc 1 gói "full" mặc định. Giữ KISS: dùng 1 slug cấu hình (env hoặc hằng) cho bản đầu.

## Requirements
- Sticky bar (chỉ hiện khi `tier==='free'`): tên gói + giá (`formatVnd`) + nút "Mở khóa báo cáo đầy đủ".
- Deep-link: `/shop/{slug}?name=&birth_day=&phone=&gender=` (hoặc đẩy customerInfo vào localStorage key đã thống nhất).
- `/shop/[slug]`: đọc prefill (query ưu tim, fallback store/localStorage) → đổ vào form state; nếu đủ field, cho "Mua ngay" luôn.
- Banner CTA + per-card CTA → dùng chung 1 handler `goToUnlock()`; bỏ trùng lặp text.

## Architecture
```
/ket-qua (free) ─ StickyPurchaseBar(gói, giá) ─ goToUnlock()
   goToUnlock → router.push(/shop/{slug}?prefill từ customerInfo)
/shop/[slug] → useEffect đọc prefill → setForm → (đủ data) enable Mua ngay
```

## Related code files
**Modify**
- `Numerology-Landing-Page/src/pages/ket-qua/index.tsx` — thêm `StickyPurchaseBar`; `goToUnlock` chung.
- `Numerology-Landing-Page/src/modules/result/BannerSearchResultPage.tsx` — CTA dùng `goToUnlock`.
- `Numerology-Landing-Page/src/modules/result/NumberCard.tsx` / `LockCard` — CTA dùng `goToUnlock`.
- `Numerology-Landing-Page/src/pages/shop/[slug].tsx` — đọc prefill → fill form.
**Create**
- `Numerology-Landing-Page/src/modules/result/parts/StickyPurchaseBar.tsx`.
- (tùy) `Numerology-Landing-Page/src/lib/checkout-prefill.ts` — encode/decode prefill (query + localStorage), 1 nguồn.

## Implementation steps
1. `checkout-prefill.ts`: `buildUnlockHref(slug, customerInfo)` + `readPrefill(router)` (query→store→localStorage).
2. `StickyPurchaseBar`: fetch gói gợi ý (`getProductBySlug(UNLOCK_SLUG)` hoặc `listProducts('report')[0]`), hiện giá; chỉ render khi free.
3. Nối banner + lock-card CTA vào `goToUnlock` (dùng `buildUnlockHref`).
4. `/shop/[slug]`: `readPrefill` trong useEffect → set form; validate; nếu đủ → không bắt nhập lại.
5. Compile + click-through thử luồng free → /shop prefilled.

## Todo
- [ ] checkout-prefill helper
- [ ] StickyPurchaseBar
- [ ] CTA hợp nhất (banner + card)
- [ ] /shop/[slug] đọc prefill
- [ ] compile + manual flow

## Success criteria
- Từ /ket-qua bấm mở khóa → /shop/[slug] đã điền sẵn name/birthday/phone(/gender), không gõ lại.
- Chỉ 1 thông điệp upsell mạch lạc (sticky bar) + hint nhẹ ở lock-card.

## Risks
- Slug gói gợi ý hardcode → để 1 hằng/env, ghi chú để sau map động theo số chủ đạo.
- Prefill PII trên URL — cân nhắc localStorage thay vì query nếu lo lộ trên history.

## Next
→ Phase 05 PDF qua fulfillment.
