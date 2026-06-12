# Phase 03 — Macros + chèn biểu đồ vào template

**Priority:** High · **Status:** ✅ complete · **Depends:** 01, 02

## Overview
Hiển thị 4 biểu đồ trong PDF. Tập trung ở `_macros.html` (macro `chart_block`) + `base_report.html` (block dùng chung cho `reports/*`) + `invoice.html`/`invoice-free.html` (path direct).

## Key insights
- `reports/report-{overview,love,career,mini}.html` đều `extends base_report.html` → thêm 1 section charts ở base là phủ cả 4.
- `invoice.html`/`invoice-free.html` KHÔNG extend base (standalone) → chèn trực tiếp.
- SVG đã dựng sẵn ở Python → template chỉ `{{ ... | safe }}` trong wrapper.

## Related code files
- **Modify:** `app/templates/reports/_macros.html` (thêm `chart_block`)
- **Modify:** `app/templates/reports/base_report.html` (section charts sau cover/trước content)
- **Modify:** `app/templates/invoice.html` (chèn 4 chart, cạnh birth_chart hiện có)
- **Modify:** `app/templates/invoice-free.html` (subset/đủ theo data)
- **Verify (no edit needed):** `report-overview/love/career/mini.html` (kế thừa base)

## Implementation steps
1. **Macro** `chart_block(title, subtitle, svg)` trong `_macros.html`: section `.new-page .section .chart-page` + `h1.section-title` + subtitle + `<div class="chart-wrap">{{ svg|safe }}</div>`. Guard caller `{% if svg %}`.
2. **base_report.html**: thêm `{% block charts %}` (mặc định render 4 chart nếu `charts`):
   ```jinja
   {% if charts %}
   {{ m.chart_block("Biểu đồ sức mạnh", "Tần suất các con số", charts.power) }}
   {{ m.chart_block("Bản đồ năng lượng cốt lõi", "Radar các chỉ số", charts.radar) }}
   {{ m.chart_block("Hành trình các Đỉnh cao", "Theo từng giai đoạn tuổi", charts.timeline) }}
   {{ m.chart_block("Vòng chu kỳ 9 năm", "Năm cá nhân hiện tại", charts.wheel) }}
   {% endif %}
   ```
   Đặt block sau cover, trước `{% block content %}`.
3. **invoice.html**: sau section "Biểu đồ ngày sinh"/"Biểu đồ tên", thêm 4 `m.chart_block(..., report.charts.*)`. Giữ birth_chart_svg cũ (bổ sung, không thay thế).
4. **invoice-free.html**: chèn tương tự (Phase đã chốt free cũng đủ 4 — nếu data nghèo, vẫn render, cột/đồ thị 0).
5. Đảm bảo `m` được import ở mọi template (base + invoice đã `import _macros as m`).

## Edge cases
- `charts` None → block không render (guard `{% if charts %}`).
- 1 chart lỗi/None lẻ → `chart_block` guard `{% if svg %}` bỏ qua riêng nó.

## Todo
- [ ] `chart_block` macro
- [ ] base_report.html `{% block charts %}`
- [ ] invoice.html chèn 4 chart
- [ ] invoice-free.html chèn chart
- [ ] Render thử HTML (debug route `numerology_free` preview) kiểm 4 chart xuất hiện
- [ ] Render PDF 1 mẫu mỗi template

## Success criteria
- 4 biểu đồ hiện đúng trong PDF của: invoice, invoice-free, report-overview/love/career/mini.
- Thiếu data → không vỡ layout.

## Risks
- Page break: mỗi chart 1 `.new-page` có thể tốn trang → cân nhắc gộp 2 chart/trang (đánh giá ở QA Phase 06).
