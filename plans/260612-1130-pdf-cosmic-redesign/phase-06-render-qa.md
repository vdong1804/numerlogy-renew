# Phase 06 — Render QA đa template + xử lý rủi ro WeasyPrint

**Priority:** High · **Status:** ✅ complete · **Depends:** 03, 04, 05

## Overview
Kiểm thử render PDF thực tế trên mọi template + dữ liệu biên; xác nhận các rủi ro WeasyPrint đã được xử lý; chạy full test suite.

## Key insights
- WeasyPrint là điểm dễ "đẹp trên HTML, hỏng trên PDF" → phải render PDF thật, không chỉ HTML.
- Test data biên: master number (11/22), tên ít số, ngày sinh nhiều số trùng, input thiếu (package-only).

## Related code files
- **Reference:** tất cả template + `report_charts.py` + `_theme.css`
- **Tests:** `tests/services/test_report_charts.py`, `test_numerology_report_builder.py`, `test_fulfillment_service.py`, `tests/integration/test_numerology_endpoints.py`
- **Tooling:** debug preview route `GET` trong `numerology_free.py` (HTML); render PDF qua script/endpoint.

## Checklist QA (render PDF thật mỗi mục)
1. `invoice.html` (paid full) — 4 chart + cosmic + ornament OK.
2. `invoice-free.html` (free route) — chart hiển thị, layout không vỡ.
3. `reports/report-overview.html` (fulfillment) — charts từ calc tính ở Phase 02.
4. `reports/report-love.html`, `report-career.html` — kế thừa base, charts OK.
5. `reports/report-mini.html` — bản free fulfillment.
6. Input thiếu name/birth_day → KHÔNG có chart, KHÔNG crash.

## Rủi ro cần xác nhận đã xử lý
- [ ] **Glow**: dùng radial-gradient (không `filter: blur`) → render đúng trên PDF.
- [ ] **Glyph chiêm tinh**: dùng SVG ornament, không unicode astro thiếu font.
- [ ] **Master 11/22**: radar/charts không vỡ thang, nhãn đúng.
- [ ] **Nền tối điểm nhấn**: chỉ cover/chương/chart; nội dung cream đọc tốt.
- [ ] **Page break**: chart không bị cắt giữa; cân nhắc gộp chart/trang nếu thừa trang.
- [ ] **Dung lượng PDF**: so trước/sau, đảm bảo không phình bất thường.
- [ ] **Thời gian render**: đo, không tăng đáng kể (SVG ~ms).

## Implementation steps
1. Viết/ chạy script render mẫu cho 6 trường hợp (lưu PDF tạm để xem).
2. Mở từng PDF, đối chiếu checklist (dùng `ck:ai-multimodal` mô tả nếu cần soi nhanh).
3. Fix lỗi render phát hiện (lặp với Phase 03/04 nếu cần).
4. `pytest` toàn bộ liên quan → xanh.
5. (Optional) `code-reviewer` review thay đổi.

## Todo
- [ ] Render 6 mẫu PDF
- [ ] Đối chiếu checklist rủi ro
- [ ] Fix lỗi
- [ ] Full test suite pass
- [ ] Cập nhật docs nếu có (docs/ + changelog)

## Success criteria
- 6 mẫu render đẹp & đúng; mọi rủi ro tick; tests pass; không regression download/fulfillment.

## Risks
- Phát hiện muộn lỗi WeasyPrint → buffer thời gian; ưu tiên render PDF sớm (có thể kéo 1 lần render lên cuối Phase 03).
