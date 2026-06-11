# Brainstorm: Redesign báo cáo Thần Số Học (đẹp hơn + ảnh Gemini)

**Date:** 2026-06-11 · **Status:** Approved · **Next:** `/ck:plan`

## Problem statement

Báo cáo Thần số học hiện đơn điệu. Yêu cầu: thiết kế lại đẹp/sinh động hơn, dùng Gemini gen ảnh.

## Hiện trạng (scout)

- Template HTML: `invoice.html` (paid), `invoice-free.html` (free) → PDF qua **wkhtmltopdf** (`pdfkit`) tại `app/utils/pdf.py`.
- Data: `numerology_full_report.py` → `build_report_view()` (dict: header/summary/chart_grid/chart_sections/sections).
- Render dùng ở: `routers/numerology_free.py`, `routers/numerology_paid.py`, `services/fulfillment_service.py`.
- Design hiện tại: Roboto Serif, navy `#002060` + đỏ `#c0392b`, layout `<table>`, page-break thủ công.
- `google-genai>=0.3` + `python-docx` đã có sẵn deps. `pdfkit` sẽ gỡ.

## Điểm nghẽn gốc rễ (brutal honesty)

**wkhtmltopdf = WebKit 2012** → không hỗ trợ flexbox/grid, CSS var, box-shadow/gradient hiện đại, web font flaky. Trần thẩm mỹ thấp → không thể "đẹp thật" nếu giữ engine này, dù ảnh đẹp tới đâu.

## Quyết định đã chốt

| Hạng mục | Lựa chọn |
|---|---|
| PDF engine | **WeasyPrint** (thay wkhtmltopdf) |
| Ảnh Gemini | **Cả hai**: thư viện tĩnh pre-gen + bìa per-user |
| Phạm vi | **Cả 2 template** (free+paid), full redesign |
| Theme | **Huyền bí/thiên văn**: navy `#002060` + gold `#C9A227` |
| Triển khai | **Toàn bộ 4 phase** |
| Dev env | **Test render qua Docker** (tránh cài GTK trên Windows) |

## Giải pháp

### 1. Engine swap (WeasyPrint)
- Chỉ sửa `app/utils/pdf.py`: `pdfkit.from_string()` → `weasyprint.HTML(string=html).write_pdf()`. Giữ nguyên signature `render_pdf()`/`render_html()` → router/fulfillment không đổi.
- `pyproject.toml`: gỡ `pdfkit`, thêm `weasyprint`. Dockerfile: thêm system deps (pango/cairo/gdk-pixbuf).
- WeasyPrint hỗ trợ `@page` margin boxes → số trang tự động, running header/footer.

### 2. Design system (theme huyền bí)
- Màu: navy `#002060` + gold `#C9A227` + kem `#FBF8F0` + son `#B0392B`.
- Font: Roboto Serif (body) + serif display (Cormorant/Playfair) cho heading.
- Hoạ tiết: viền sacred-geometry, chòm sao footer, divider vàng.
- Tokens gom `reports/_theme.css` dùng chung 2 template (DRY).

### 3. Pipeline ảnh
**🔑 Insight:** KHÔNG để AI render chữ Việt (sai dấu). AI chỉ gen nghệ thuật trừu tượng → overlay tên/ngày sinh bằng CSS đè lên.

- **Thư viện tĩnh** (gen 1 lần, lưu static): 11 archetype (số chủ đạo 1-9,11,22) + 3-4 divider + 1 bìa fallback. ~15-18 ảnh, chi phí vài $. Dùng `ai-multimodal` skill.
- **Bìa per-user** (fulfillment, paid): gen nền theo số chủ đạo, **cache theo `so_chu_dao`** (tái dùng → tiết kiệm). Overlay text bằng CSS. **Fail-safe:** lỗi/timeout → fallback bìa tĩnh → không block thanh toán.
- **Biểu đồ ngày sinh:** SVG deterministic (không AI) → chính xác + nhẹ.

### 4. Template restructure (cả 2 bản)
- `base_report.html` mới: `_theme.css`, `@page` header/footer + số trang.
- Cover (ảnh nền + overlay), mục lục (paid), tổng quan dạng card grid, SVG chart, section "Số chủ đạo" có hero archetype, các section có divider/drop-cap/blockquote, CTA box (free).

## Phased rollout
1. **P1** Swap WeasyPrint, verify design cũ không vỡ.
2. **P2** Design system + restructure template (chưa cần ảnh AI).
3. **P3** Gen thư viện ảnh tĩnh + tích hợp archetype/divider/SVG chart.
4. **P4** Bìa per-user + cache theo số chủ đạo + fail-safe.

## Risks & mitigation
- WeasyPrint Windows dev khó → test qua Docker.
- Per-user gen latency/cost/fail → cache theo số chủ đạo + fallback tĩnh + timeout.
- AI render chữ Việt sai → overlay text bằng CSS, AI chỉ gen art.
- Regression PDF prod → P1 verify trước khi đổi design.
- Web font trong WeasyPrint → nhúng `@font-face` local (không phụ thuộc CDN lúc render).

## Success criteria
- PDF render đúng qua WeasyPrint (cả free+paid), không lỗi layout.
- Báo cáo có cover ảnh, archetype theo số chủ đạo, SVG chart, theme navy+gold đồng bộ.
- Bìa per-user gen + cache hoạt động, có fallback khi fail.
- Fulfillment/thanh toán không bị block bởi gen ảnh.

## Unresolved questions
- Imagen 4 hay Nano Banana cho chất lượng/giá tối ưu? (chốt ở P3 khi test thực tế)
- Lưu ảnh per-user ở MEDIA_ROOT path nào + chính sách cache TTL?
- Có cần đồng bộ design này sang bản DOCX export (`build_report_docx.py`) không?
- Font display cụ thể (Cormorant vs Playfair) — chọn khi dựng theme.
