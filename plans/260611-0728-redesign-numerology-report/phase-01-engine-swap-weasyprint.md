---
phase: 1
title: Engine Swap WeasyPrint
status: completed
priority: P1
effort: 0.5d
dependencies: []
---

# Phase 1: Engine Swap WeasyPrint

## Context Links
- Design doc: `plans/reports/brainstorm-260611-0728-redesign-numerology-report.md`
- Render util: `app/utils/pdf.py`

## Overview
Thay engine PDF `wkhtmltopdf`(`pdfkit`) → **WeasyPrint** mà KHÔNG đổi giao diện hàm `render_pdf()`/`render_html()`, để mọi caller (routers + fulfillment) hoạt động nguyên trạng. Verify design cũ render đúng trước khi đụng tới thẩm mỹ (P2).

## Requirements
- Functional: `render_pdf(template_name, context)` trả về PDF bytes như cũ; `render_html()` giữ nguyên. Cả `invoice.html`, `invoice-free.html`, `reports/*.html`, `invoice-order.html` render được.
- Non-functional: không block event loop (giữ `asyncio.to_thread`); fonts tiếng Việt hiển thị đúng dấu; build Docker thành công.

## Architecture
- `pdfkit.from_string(html, options=...)` → `weasyprint.HTML(string=html, base_url=...).write_pdf()`.
- `base_url` = `_get_base_dir()` để WeasyPrint resolve asset tương đối (thay cơ chế `file://{{base_dir}}` + `enable-local-file-access` của wkhtmltopdf). Kiểm tra template nào đang dùng `file://` path → đổi sang relative/`base_url`.
- Margin/page-size: chuyển `_PDF_OPTIONS` (Letter, margin) sang CSS `@page { size: Letter; margin: ... }` trong template/theme (P2 sẽ tinh chỉnh; P1 đặt tối thiểu để khớp output cũ).
- WeasyPrint không có `custom-header`/`Accept-Encoding` (không cần).

## Related Code Files
- Modify: `app/utils/pdf.py` — thay implementation `_run_pdfkit` → `_run_weasyprint`; bỏ import `pdfkit`.
- Modify: `pyproject.toml` — gỡ `pdfkit>=1.0`, thêm `weasyprint>=63` (kiểm tra version mới nhất).
- Modify: `Dockerfile` — gỡ pkg wkhtmltopdf-only (`wkhtmltopdf`, `libxrender1`, `libxtst6`, `xfonts-75dpi`, `xfonts-base`); thêm WeasyPrint deps: `libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info`. GIỮ fonts (`fonts-noto-cjk`, `fontconfig`, ...).
- Read context: `app/routers/numerology_free.py`, `numerology_paid.py`, `services/fulfillment_service.py`, `routers/my_account.py` (invoice-order render + cache).

## Implementation Steps
1. Khảo sát toàn bộ caller `render_pdf`/`render_html` + grep `file://`/`base_dir` trong templates để biết chỗ nào phụ thuộc cơ chế asset cũ.
2. Viết lại `app/utils/pdf.py`: `_run_weasyprint(html, base_url)`; `render_pdf` gọi `weasyprint.HTML(string=html, base_url=base_url).write_pdf()` qua `asyncio.to_thread`. Giữ logging + RuntimeError wrap.
3. Đặt `@page { size: Letter; margin: 0.3in 0.6in; }` tối thiểu (trong base template hoặc inline) để khớp margin cũ.
4. Cập nhật `pyproject.toml` + `Dockerfile` (system deps).
5. Build + run qua Docker; render thử cả 4 họ template với data thật → so sánh PDF với bản cũ (không vỡ layout, đúng dấu tiếng Việt, đúng số trang).
6. Chạy test suite hiện có (`tests/`), đặc biệt test nào chạm PDF/fulfillment.

## Todo List
- [ ] Grep caller + `file://`/`base_dir` usage trong templates
- [ ] Rewrite `app/utils/pdf.py` sang WeasyPrint
- [ ] `@page` margin tối thiểu khớp output cũ
- [ ] Update `pyproject.toml` (gỡ pdfkit, thêm weasyprint)
- [ ] Update `Dockerfile` system deps
- [ ] Build + render verify qua Docker (4 họ template)
- [ ] Chạy test suite

## Success Criteria
- [ ] `docker compose build` thành công với deps mới.
- [ ] `invoice.html`, `invoice-free.html`, `reports/*.html`, `invoice-order.html` render PDF không lỗi, đúng dấu tiếng Việt.
- [ ] Số trang / ngắt trang hoạt động (page-break-before giữ nguyên).
- [ ] Không còn import `pdfkit`; test suite pass.

## Risk Assessment
- **Asset path khác cơ chế**: wkhtmltopdf dùng `file://` + flag; WeasyPrint dùng `base_url`. → Audit kỹ ở bước 1, sửa template nếu cần.
- **Font khác render**: WeasyPrint qua Pango có thể đổi metrics/dòng. → So sánh visual, tinh chỉnh ở P2.
- **WeasyPrint version deps**: cần system libs chính xác. → Pin version, test trong Docker.
- **Regression prod**: đây là luồng tạo báo cáo trả phí. → Verify đầy đủ trước khi merge; giữ khả năng rollback (git).

## Security Considerations
- WeasyPrint fetch URL trong HTML (ảnh remote) → cân nhắc giới hạn `url_fetcher` để tránh SSRF nếu content DB có URL ngoài (theme dùng asset local nên rủi ro thấp; ghi nhận cho P3/P4).

## Next Steps
- Mở khoá P2 (design system) sau khi engine ổn định.
