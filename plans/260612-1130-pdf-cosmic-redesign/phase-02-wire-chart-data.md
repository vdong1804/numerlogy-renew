# Phase 02 — Wire chart data vào 2 context render

**Priority:** High · **Status:** ✅ complete · **Depends:** 01

## Overview
Đưa output `build_charts()` vào **cả 2 đường render** để mọi report có biểu đồ. Fail-safe tuyệt đối (không crash fulfillment).

## Key insights
- Path direct (`invoice.html`/`invoice-free.html`) đã có `calc` trong `build_report_view()` → chỉ thêm key `charts`.
- Path fulfillment (`reports/report-*.html`) KHÔNG có calc → tính từ `input_payload` (name + birth_day, đã dùng cho cover). `calculate_numerology_numbers()` rẻ, không DB.

## Related code files
- **Modify:** `app/services/numerology_full_report.py` (`build_report_view` → thêm `"charts"`)
- **Modify:** `app/services/fulfillment_service.py` (`_render_report_pdf` → tính calc + charts vào context, guarded)
- **Reference:** `app/routers/numerology_paid.py:90-95`, `numerology_free.py:93-98`, `fulfillment_service.py:255-316` (`_render_report_pdf`, `_resolve_cover_bg`)
- **Tests:** `tests/services/test_numerology_report_builder.py`, `tests/services/test_fulfillment_service.py`

## Implementation steps
1. **build_report_view**: trước `return`, thêm `"charts": build_charts(calc, birth_day)` (import từ `report_charts`). → cover `invoice.html` + `invoice-free.html` + debug preview.
2. **fulfillment_service._render_report_pdf**:
   - Tách helper `_resolve_chart_charts(input_payload) -> dict|None` (giống `_resolve_cover_bg`): lấy name+birth_day; nếu đủ → `calculate_numerology_numbers` → `build_charts`; lỗi/thiếu → `None`, log warning, KHÔNG raise.
   - Thêm `"charts": await ...` (hoặc sync, build_charts thuần CPU → gọi trực tiếp, không cần thread) vào `context`.
3. **Xác nhận template đích bản free/mini:** kiểm tra `product.template_name` của sku `report-mini-free` (seed `scripts/seed_products.py`) → biết nó dùng `report-mini.html` (fulfillment) hay route `invoice-free.html`. Ghi kết quả vào plan/notes. Đảm bảo template đó nhận `charts`.
4. Guard template: chart chỉ render khi `charts` truthy (Phase 03 lo phần template `{% if charts %}`).

## Edge cases
- input_payload thiếu name/birth_day (gói thuần package) → charts=None → template bỏ qua.
- birth_day định dạng lạ → `calculate_numerology_numbers` raise → catch → None.
- master number → đã xử lý ở Phase 01.

## Todo
- [ ] `build_report_view` thêm `charts`
- [ ] `fulfillment_service` helper `_resolve_chart_charts` + inject context (fail-safe)
- [ ] Xác nhận template_name của `report-mini-free`
- [ ] Test: build_report_view trả `charts` đủ 4 key
- [ ] Test: fulfillment context có `charts` khi input hợp lệ; `None` khi thiếu (không raise)
- [ ] `pytest tests/services/`

## Success criteria
- Cả 2 path đưa `charts` vào context; thiếu input không crash; tests pass.

## Security/Risk
- Không log PII (name/birth_day) ở mức info.
- `build_charts` đồng bộ, nhanh → không block event loop đáng kể; nếu lo, `asyncio.to_thread`.
