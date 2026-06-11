---
phase: 2
title: Design System & Template Restructure
status: completed
priority: P1
effort: 1.5d
dependencies:
  - 1
---

# Phase 2: Design System & Template Restructure

## Context Links
- Design doc: `plans/reports/brainstorm-260611-0728-redesign-numerology-report.md`
- Templates: `app/templates/invoice.html`, `invoice-free.html`, `reports/base_report.html`, `reports/report-*.html`

## Overview
Dựng design system "huyền bí/thiên văn" (navy + gold) gom vào CSS dùng chung, restructure template để đẹp/cao cấp hơn: cover, card grid, divider vàng, drop-cap, SVG biểu đồ ngày sinh. Áp đồng bộ cho **cả 2 họ template** (invoice* và reports/*). Chưa cần ảnh AI (placeholder/khung sẵn sàng cho P3).

## Requirements
- Functional: cả `invoice.html`, `invoice-free.html`, `reports/base_report.html` (+ children) dùng chung tokens; biểu đồ ngày sinh vẽ SVG từ `chart_grid`; số trang ở footer.
- Non-functional: CSS WeasyPrint-safe (tránh feature không hỗ trợ); font nhúng `@font-face` local (không phụ thuộc CDN lúc render); giữ khả năng đọc, mật độ chữ hợp lý.

## Key Insights
- WeasyPrint hỗ trợ `@page` margin boxes (running header/footer + `counter(page)`), flexbox/grid cơ bản, gradient, border-radius, box-shadow, SVG, transform 2D, multi-column.
- **Font phải nhúng local** (`static/fonts/`) — render server-side, không nên phụ thuộc Google Fonts CDN.
- 2 họ template có data shape khác nhau (invoice* dùng `build_report_view`; reports/* dùng `content_codes`) → CSS chung, nhưng markup từng họ riêng.

## Architecture
- **`app/templates/reports/_theme.css`** (file mới) — design tokens + component styles dùng chung:
  - Tokens: `--navy:#002060; --gold:#C9A227; --cream:#FBF8F0; --vermilion:#B0392B`.
  - `@page`: size Letter, margin, `@bottom-center { content: counter(page) }`, running header thương hiệu.
  - Components: `.cover`, `.card-grid`/`.stat-card`, `.divider-gold`, `.section-title`, drop-cap (`p.lead::first-letter`), `.blockquote`, `.chart-svg`.
- Font: tải Roboto Serif + 1 serif display (Cormorant/Playfair — chốt ở đây) về `static/fonts/`, khai báo `@font-face` trong `_theme.css`.
- **SVG biểu đồ ngày sinh**: macro Jinja (vd `reports/_macros.html`) nhận `chart_grid` 3x3 → render SVG ô lưới + số, tô gold/vermilion. Deterministic, thay `<table class="chart">` cũ. Dùng được cho cả invoice* (có `chart_grid`).
- Template restructure:
  - `invoice.html` / `invoice-free.html`: link `_theme.css` (inline qua Jinja include để WeasyPrint nhúng), cover mới, summary → card grid, chart → SVG, sections có divider + drop-cap. Free giữ subset + CTA box nâng cấp.
  - `reports/base_report.html`: nâng cấp cùng tokens (đường fulfillment), giữ block structure cho children.
- Chèn placeholder `{% block hero_image %}`/biến cho ảnh archetype + cover (P3/P4 fill); P2 để trống/ảnh tạm an toàn.

## Related Code Files
- Create: `app/templates/reports/_theme.css`, `app/templates/reports/_macros.html` (SVG chart + helpers), `static/fonts/*` (font files).
- Modify: `app/templates/invoice.html`, `app/templates/invoice-free.html`, `app/templates/reports/base_report.html`, `reports/report-overview.html`, `report-mini.html`, `report-love.html`, `report-career.html`.
- Modify (nếu cần): `app/utils/pdf.py` — đảm bảo `base_url` cho `@font-face`/asset local.
- Read context: `app/services/numerology_full_report.py` (shape `chart_grid`, `summary`, `sections`).

## Implementation Steps
1. Chọn font display (Cormorant vs Playfair), tải font files về `static/fonts/`, viết `@font-face`.
2. Viết `_theme.css`: tokens, `@page` + số trang/header, component classes. Cách nhúng: include nội dung CSS vào `<style>` qua Jinja (`{% include %}`) hoặc `base_url` + `<link>` local — chọn cách WeasyPrint nhúng được.
3. Viết `_macros.html`: macro `birth_chart_svg(chart_grid)` + macro divider/section header.
4. Restructure `invoice.html`: cover, card-grid summary, SVG chart, sections (divider, drop-cap, blockquote). Để slot ảnh archetype/cover (placeholder).
5. Restructure `invoice-free.html` đồng bộ + CTA box nâng cấp.
6. Nâng cấp `reports/base_report.html` + children dùng tokens chung.
7. Render verify qua Docker với data thật (cả 2 đường) — kiểm tra layout, số trang, font, ngắt trang, mật độ chữ.
8. Tinh chỉnh các điểm WeasyPrint render khác kỳ vọng.

## Todo List
- [ ] Chọn + nhúng font display local (`@font-face`)
- [ ] `_theme.css` (tokens + @page + components)
- [ ] `_macros.html` (SVG birth chart + dividers)
- [ ] Restructure `invoice.html`
- [ ] Restructure `invoice-free.html` + CTA
- [ ] Upgrade `reports/base_report.html` + children
- [ ] Slot/placeholder ảnh archetype + cover (cho P3/P4)
- [ ] Render verify qua Docker (2 đường, data thật)

## Success Criteria
- [ ] Theme navy+gold đồng bộ trên cả invoice* và reports/* khi xuất PDF.
- [ ] Biểu đồ ngày sinh là SVG (không phải table phẳng), số đúng theo `chart_grid`.
- [ ] Footer có số trang; cover mới hiển thị đúng tên/ngày sinh.
- [ ] Font display + body load local, đúng dấu tiếng Việt, không phụ thuộc CDN.
- [ ] Slot ảnh sẵn sàng (placeholder không vỡ layout khi chưa có ảnh).

## Risk Assessment
- **CSS không tương thích WeasyPrint** (vài thuộc tính grid/flex nâng cao): → giữ layout đơn giản, test sớm, có fallback table khi cần.
- **Font embedding fail** → text vỡ: → verify `@font-face` local + `base_url` đúng.
- **2 họ template phình code/lệch nhau**: → tối đa hoá phần dùng chung qua `_theme.css` + `_macros.html` (DRY); markup riêng tối thiểu.
- **Mật độ nội dung dài** (sections nhiều) ngắt trang xấu: → dùng `break-inside: avoid` cho card/section title.

## Security Considerations
- Nội dung DB render qua `|safe` (rich-text tin cậy) — giữ nguyên; không introduce nguồn HTML mới không tin cậy.

## Next Steps
- P3 fill ảnh archetype/divider vào slot đã chừa.
