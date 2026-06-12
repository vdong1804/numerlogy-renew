# Phase 05 — Frontend: PDF via Fulfillment (bỏ /api/so-hoc)

**Context:** `plan.md` · Phase 01-04
**Priority:** Med · **Status:** ⬜ Not started

## Overview
Thay `/api/so-hoc` (PDF cũ) bằng PDF render từ **template fulfillment** (`invoice-free`/`invoice`).
Free **vẫn tải được** bản rút gọn (invoice-free, KHÔNG cần order); paid tải bản đầy đủ từ order. Fix copy + typo (#3, #5).

## Decisions (Q3)
- Free → tải PDF rút gọn qua endpoint **public** render `invoice-free` (no auth, no order).
- Paid → tải PDF đầy đủ từ order fulfillment.
- 1 bộ template fulfillment cho cả hai (bỏ template/đường `/api/so-hoc` cũ).

## Key insights
- `BoxExportPDF` hiện vừa nói "nâng cấp VIP để tải" vừa tải free ngay → mâu thuẫn. Cần 2 trạng thái theo `tier`.
- Cần endpoint backend mới render `invoice-free` từ name+birth_day không cần order (tái dùng `fulfillment_service._render_report_pdf` / `build_report_view`).

## Requirements
**Backend**
- Endpoint public `GET /api/numerology-report/pdf` (free) → render `invoice-free.html` từ name+birth_day, trả `application/pdf`. Tái dùng render path fulfillment, KHÔNG tạo bộ sinh PDF thứ 2.
- (paid) tải PDF đầy đủ từ order: xác nhận/ți dùng route trong `routers/orders.py` (fulfillment delivery). Nếu chưa có route tải trực tiếp → thêm `GET /api/orders/{id}/report.pdf` (auth, owner-only, chỉ khi paid).
**Frontend**
- `tier === 'free'`: `BoxExportPDF` nút "Tải bản PDF rút gọn" → endpoint free-pdf; kèm hint "Mở khóa để nhận bản đầy đủ" → `goToUnlock()`.
- `tier === 'paid'`: nút "Tải báo cáo PDF đầy đủ" → order PDF.
- Bỏ `getMainstreamPDF`/`/api/so-hoc` khỏi /ket-qua (grep usage nơi khác trước khi xóa định nghĩa).
- Fix typo "thần số **sọc**" → "thần số **học**" (`BoxExportPDF.tsx`).

## Architecture
```
BoxExportPDF(tier, orderId?)
  free → GET /api/numerology-report/pdf?full_name&birth_day  (invoice-free)  + hint goToUnlock()
  paid → GET /api/orders/{id}/report.pdf  (invoice, owner-only)
```

## Related code files
**Inspect**
- `numerology-api/app/services/fulfillment_service.py` + `app/routers/orders.py` — tìm route tải PDF của order đã paid (có thể là delivery/email/asset). Nếu chưa có endpoint tải trực tiếp → ghi chú bổ sung (có thể là phase phụ backend nhỏ).
**Modify**
- `Numerology-Landing-Page/src/modules/result/parts/BoxExportPDF.tsx` — 2 trạng thái theo tier; fix copy/typo.
- `Numerology-Landing-Page/src/pages/ket-qua/index.tsx` — bỏ `handleDownloadPDF`/`getMainstreamPDF`; truyền `tier`/`orderId` vào BoxExportPDF.
- (tùy) `Numerology-Landing-Page/src/lib/shop-api.ts` — thêm `getOrderReportPdf(orderId)` nếu cần.

## Implementation steps
1. Grep `getMainstreamPDF` / `/api/so-hoc` toàn FE → xác định nơi dùng; chỉ gỡ khỏi /ket-qua.
2. Xác nhận route tải PDF của order paid (đọc `routers/orders.py`, `fulfillment_service`). Nếu thiếu → note open question / phase phụ.
3. `BoxExportPDF`: nhận `tier`, `orderId?`; render CTA tương ứng; fix copy + typo.
4. Page: bỏ state `isLoadingPDF`/handler cũ; nối tier/orderId.
5. Compile + thử free (CTA) vs paid (download).

## Todo
- [ ] grep usage /api/so-hoc
- [ ] xác nhận route order PDF
- [ ] BoxExportPDF 2 trạng thái + fix typo
- [ ] page bỏ handler cũ
- [ ] compile + manual

## Success criteria
- /ket-qua không còn gọi `/api/so-hoc`.
- Free: bấm tải → dẫn tới mua. Paid: tải đúng PDF fulfillment.
- Copy nhất quán, hết typo.

## Risks
- Có thể chưa có endpoint tải PDF trực tiếp cho order (fulfillment qua email/asset) → cần làm rõ; nếu vậy thêm route nhỏ ở backend (escalate).

## Open questions
- Order paid trả PDF qua đâu (download trực tiếp / link email / asset store)?
- Bản teaser PDF free có giữ không, hay free chỉ xem on-screen?

## Next
→ Phase 06 tests + docs.
