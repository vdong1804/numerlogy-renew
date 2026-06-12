---
status: complete
created: 2026-06-12
completed: 2026-06-12
slug: pdf-cosmic-redesign
---

# Plan — Báo cáo PDF "Cosmic" + 4 biểu đồ + hình ảnh hybrid

Nâng cấp báo cáo PDF Numerology: thẩm mỹ **vũ trụ huyền bí (Cosmic, dạng điểm nhấn)**, thêm **4 biểu đồ SVG**, **hình ảnh hybrid**. Áp dụng **tất cả report**.

**Brainstorm:** `plans/reports/brainstorm-260612-pdf-cosmic-redesign.md`
**Stack:** Jinja2 + WeasyPrint (no JS) → chart = inline SVG server-side.

## Kiến trúc then chốt (đã verify scout)

2 đường render PDF, **context khác nhau** → cần 1 builder chung `build_charts(calc)`:

| Đường | Template | Context | calc? |
|---|---|---|---|
| Direct route (`numerology_paid/free.py`) | `invoice.html`, `invoice-free.html` | `{report}` từ `build_report_view()` | ✅ có |
| **Order fulfillment** (`fulfillment_service`) | `reports/report-{overview,love,career,mini}.html` (extend `base_report.html`) | `{content, input}` chỉ DB rows | ❌ **thiếu** |

→ Path direct: thêm `charts` vào `build_report_view()`. Path fulfillment: tính `calc` từ `input_payload` (đã có name/birth_day) rồi `build_charts()`. Cả 2 dùng chung module → DRY.

## Phases

| # | Phase | Status | Depends |
|---|---|---|---|
| 01 | [Chart engine `report_charts.py` + tests](phase-01-chart-engine.md) | ✅ complete | — |
| 02 | [Wire chart data vào 2 context](phase-02-wire-chart-data.md) | ✅ complete | 01 |
| 03 | [Macros + chèn template (invoice + base_report)](phase-03-template-integration.md) | ✅ complete | 01,02 |
| 04 | [Cosmic theme (@page, starfield, glow)](phase-04-cosmic-theme.md) | ✅ complete | — |
| 05 | [Thư viện ornament SVG (hybrid)](phase-05-ornament-library.md) | ✅ complete | 04 |
| 06 | [Render QA đa template + xử lý rủi ro WeasyPrint](phase-06-render-qa.md) | ✅ complete | 03,04,05 |

## Kết quả (2026-06-12)
- Chart engine: `report_charts.py` (197 LOC) + `report_charts_geometry.py`; 12 unit tests pass.
- 2 đường render đều có `charts` (direct: `build_report_view`; fulfillment: `_resolve_charts` fail-safe).
- Macro `chart_block`/`chart_pages`; `@page chart` tối + starfield data-uri; glow radial-gradient; drop-cap; ornament SVG (corner-flourish, sacred-geometry watermark).
- QA: 6 template render PDF OK (invoice 42tr, invoice-free 15tr, report-* 6tr); Gemini visual xác nhận 4 chart legible, không clip (fix radar viewBox 360→420). `charts=None` không crash. Master number giữ nhãn (Sứ mệnh 11).
- Tests: 334 pass (1 fail không liên quan: chat `test_llm_service` DEEPSEEK_API_KEY env). Code review: SHIP-READY, 0 critical/major.
- Free report: đã trim còn **2 chart (sức mạnh + chu kỳ 9 năm)**; radar (năng lượng cốt lõi) + timeline (đỉnh/thử thách) để dành bản đầy đủ → khớp CTA upsell.

## Nguyên tắc
- YAGNI/KISS/DRY. SVG tay (KHÔNG matplotlib). Glow = `radial-gradient` (KHÔNG `filter` blur). Glyph = SVG (KHÔNG unicode astro).
- Mọi thay đổi context phải **fail-safe** (thiếu input → skip chart, không crash fulfillment).
- File code ≤200 dòng; tách module nếu vượt.

## Open questions (resolved trong plan)
- ✅ Template wiring: đã xác định 2 path ở trên.
- ✅ Free/mini thiếu calc: path fulfillment phải tính calc từ input_payload (Phase 02).
- ⚠️ Còn lại: bản free/mini delivery dùng `report-mini.html` qua fulfillment hay `invoice-free.html` qua route? → Phase 02 xác nhận `product.template_name` của `report-mini-free` để biết template đích.
