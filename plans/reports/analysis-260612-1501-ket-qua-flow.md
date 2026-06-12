# Analysis — /ket-qua Flow Review (content / packages / PDF)

**Date:** 2026-06-12 · **Scope:** `Numerology-Landing-Page/src/pages/ket-qua/index.tsx` + `src/modules/result/*` + liên đới backend report/order/fulfillment.

## Current flow
- `customerInfo` (zustand) ← bước tra cứu (name/birthDay/phone).
- `/ket-qua`: `useSWR getNumerologyReport(params)` → `/api/numerology-report` (public, trả full).
- Render sections với `IS_VIP = false` (hardcode trong page).
- Free: NumberCard blur CSS + CTA "Nâng cấp VIP →" → `/shop`. Banner CTA → `/shop`.
- Cuối trang `BoxExportPDF` Download → `getMainstreamPDF` → `/api/so-hoc` (PDF cũ).
- Luồng bán thật tách rời: `/shop` → `/shop/[slug]` (nhập lại data) → `createOrder` (auth) → `/check-out/[orderId]` → `fulfillment_service` render invoice/invoice-free.

## Findings (severity)
1. **[High] `IS_VIP=false` hardcode** — không có check entitlement; người đã mua vẫn bị khóa. VIP path chết.
2. **[High] Content leak** — full HTML luận giải trả xuống client free, chỉ che bằng `maskImage` CSS (`NumberCard.tsx:73-89`). Mở DevTools đọc được hết → gating vô giá trị, lộ nội dung trả phí.
3. **[High] Hai bộ sinh PDF tách rời** — nút Download gọi `/api/so-hoc` (cũ), KHÔNG dùng fulfillment (`invoice-free/invoice.html`) vừa redesign 2026-06-12. Bất nhất.
4. **[Med] Mất dữ liệu giữa luồng** — user đã nhập name/birthday/phone, nhưng `/shop/[slug]` (report type) bắt nhập lại cả giới tính. Friction → rớt đơn.
5. **[Med] Copy mâu thuẫn** — `BoxExportPDF` nói "Bằng cách nâng cấp VIP, bạn có thể tải về…" nhưng Download tải free ngay. Typo "thần số **sọc**" (`BoxExportPDF.tsx:31`).
6. **[Med] Gating dàn đều + CTA lặp** — mọi card (7 cốt lõi, 4 đỉnh, 4 thử thách, nợ nghiệp, 2 chu kỳ, số thiếu) đều blur + cùng 1 CTA → nhiễu, không phân tầng teaser.
7. **[Low] Thiếu giá/gói + thanh mua** — không hiển thị gói/giá; box PDF nằm tận cuối sau chuỗi card blur.

## Backend facts (cho việc nối luồng)
- `numerology_report.py`: endpoint **public, no auth**, trả mọi indicator.
- `order.py`: Order gắn `user_id` (cần auth Bearer), có `meta`/input_payload, status `paid`; OrderItem→Product.
- Product (`shop-api.ts`): có `content_codes[]`, `template_name`, `type` (package|report|combo) → nguồn unlock.
- `fulfillment_service` render PDF từ order input_payload + product → bản free chỉ power + 9-year cycle chart (changelog 2026-06-12).

## Recommendation (đã chốt)
Entitlement theo order paid khớp name+birthday → backend chỉ trả content section được mở (teaser cho phần khóa) → FE render lock-card thật + sticky CTA deep-link gói tương ứng (prefill customerInfo) → PDF chỉ qua fulfillment.

## Open questions
- `/ket-qua` có bắt buộc login để mở khóa? (order cần auth).
- Chuẩn hóa match name+birth_day (bỏ dấu/lowercase/trim)?
- Bản teaser PDF free có cho tải không, hay chỉ sau khi tạo order?
