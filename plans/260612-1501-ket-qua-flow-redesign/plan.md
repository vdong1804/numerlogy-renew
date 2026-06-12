# /ket-qua Flow Redesign — Entitlement, Content Gating, PDF Unification

**Branch:** `feat/numerology-report-gaps` · **Created:** 2026-06-12 · **Owner:** TBD

## Problem
`/ket-qua` flow không hợp lý ở 3 trục: hiển thị content, các gói (upsell), và download PDF.
Chi tiết review: `plans/reports/analysis-260612-1501-ket-qua-flow.md` (xem mục Findings dưới).

## Decisions (đã chốt với user)
1. **Entitlement** = theo **order đã mua** (không hardcode `IS_VIP`).
2. **Chống leak** = backend **không trả** nội dung phần khóa (chỉ teaser), thay vì blur CSS.
3. **PDF** = bỏ `/api/so-hoc`; mọi PDF qua **fulfillment** (invoice-free/invoice — bản redesign 2026-06-12).
4. **Scope** = plan chi tiết trước, duyệt rồi mới code.

## Core architectural constraint
- Orders cần **auth** (`user_id`, Bearer). `/ket-qua` hiện **ẩn danh** → phải nối login + match
  `input_payload (name+birth_day)` của order `paid` với báo cáo đang xem.
- Product có `content_codes` (section nào mở) + `type` (package/report/combo) → nguồn quyết định unlock.
- `/api/numerology-report` hiện **public, trả full** → phải thành **entitlement-aware**.

## Target flow
```
/ket-qua (customerInfo) ──► GET /numerology-report  (+ optional Bearer)
   backend resolve entitlement: paid order khớp name+birthday → unlocked content_codes
   → trả FULL cho section mở, {locked:true, teaser} cho section khóa (KHÔNG kèm HTML đầy đủ)
   FE: render full + lock-card thật; sticky CTA bar (gói + giá) → /shop/[slug]?prefill
   PDF: bỏ nút free /api/so-hoc; chỉ phát qua fulfillment sau khi mua
```

## Phases
| # | File | Mô tả | Status |
|---|------|-------|--------|
| 01 | [phase-01-backend-entitlement-report-api.md](phase-01-backend-entitlement-report-api.md) | Report API nhận auth → resolve order → unlocked codes; builder strip locked content | ✅ Done (23 tests pass) |
| 02 | [phase-02-free-paid-content-map.md](phase-02-free-paid-content-map.md) | FREE/ALL_SECTIONS định nghĩa trong entitlement_service (coarse v1); invoice-free align ở Phase 05 | ✅ Folded into P01 |
| 03 | [phase-03-frontend-lock-card-ui.md](phase-03-frontend-lock-card-ui.md) | Bỏ IS_VIP hardcode; lock-card từ `locked` flag (token auto qua axiosClient); tsc sạch | ✅ Done |
| 04 | [phase-04-frontend-cta-carryover.md](phase-04-frontend-cta-carryover.md) | StickyPurchaseBar + carry-over /shop prefill (qua customerInfo store) | ✅ Done |
| 05 | [phase-05-frontend-pdf-via-fulfillment.md](phase-05-frontend-pdf-via-fulfillment.md) | Free → /api/so-hoc-free; paid → /api/my/reports/{id}/download; fix copy/typo | ✅ Done |
| 06 | [phase-06-tests-docs.md](phase-06-tests-docs.md) | 38 tests pass; changelog cập nhật | ✅ Done |

## Key dependencies
- Phase 01 ⟶ 02 (builder cần biết tập free codes) ⟶ 03/04/05 (FE phụ thuộc shape API mới).
- Auth: dùng `userFetch`/Bearer đã có ở `lib/user-api.ts` & `shop-api.ts`.

## Findings (review summary)
1. `IS_VIP=false` hardcode → gating giả, user đã mua vẫn bị khóa.
2. Content trả phí gửi full xuống client, chỉ blur CSS → leak + vô giá trị.
3. Nút Download gọi `/api/so-hoc` (PDF cũ), tách rời fulfillment mới → 2 bộ sinh PDF.
4. Mất dữ liệu: /shop/[slug] bắt nhập lại name/birthday/phone/gender.
5. Copy mâu thuẫn: BoxExportPDF nói "nâng cấp VIP để tải" nhưng tải free ngay. Typo "thần số sọc".
6. Blur dàn đều mọi card + CTA lặp → nhiễu, không phân tầng teaser.
7. Không hiển thị giá/gói; thanh mua nằm tận cuối trang.

## Resolved (2026-06-12)
- **Q1:** Free xem **ẩn danh**; muốn mở khóa thì **login** (order cần auth).
- **Q2:** Chuẩn hóa match: name = bỏ dấu + lowercase + trim + gộp khoảng trắng; birth_day = 8 digits.
- **Q3:** Free **vẫn tải được PDF rút gọn** (template `invoice-free`, KHÔNG cần order); PDF đầy đủ qua order fulfillment.
  → `/api/so-hoc` bị thay bằng endpoint free-pdf render `invoice-free` (public, no order). Thống nhất 1 bộ template fulfillment.
