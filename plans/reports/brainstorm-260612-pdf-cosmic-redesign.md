# Brainstorm — Cải tiến báo cáo PDF "bí hiểm" (Cosmic) + biểu đồ + hình ảnh

**Date:** 2026-06-12 · **Status:** Agreed, ready for `/ck:plan`
**Scope:** Numerology PDF report redesign (`numerology-api`)

---

## 1. Problem statement

Báo cáo PDF hiện tại đã có nền tảng tốt (navy+gold "celestial", WeasyPrint) nhưng:
- Thiếu chiều sâu thị giác → chưa đủ cảm giác "bí hiểm/huyền học".
- Chỉ có 1 biểu đồ (birth-chart 3×3 SVG). Nhiều dữ liệu số phong phú **chưa được trực quan hóa**.
- Hình ảnh tối thiểu (cover AI + archetype tĩnh).

**Mục tiêu:** Nâng tầm thẩm mỹ theo hướng **vũ trụ huyền bí (Cosmic)**, thêm **4 biểu đồ**, bổ sung **hình ảnh hybrid** — áp dụng **tất cả report**.

---

## 2. Hiện trạng (đã scout)

| Thành phần | Trạng thái |
|---|---|
| Engine | Jinja2 + **WeasyPrint** (KHÔNG có JS → chart phải render SVG/PNG server-side) |
| Theme | `_theme.css` navy+gold, `@page cover` full-bleed, divider vàng, `::first-letter` OK |
| Chart | Chỉ `birth_chart_svg` (3×3) inline trong `_macros.html` |
| Ảnh | Cover AI (`cover_generator.py`, Vertex, cache theo số, fail-safe) + archetype tĩnh (`report_assets.py`) |
| **Dữ liệu** | `build_report_view()` đã trả `calc` đầy đủ vào context PDF: digit counts, 5+ số cốt lõi, 4 đỉnh cao + tuổi, 4 thử thách, năm cá nhân 1-9 |

**Kết luận then chốt:** Toàn bộ dữ liệu cho 4 biểu đồ **đã có sẵn trong context** → đây là việc *trình bày*, không phải plumbing dữ liệu (rủi ro tích hợp thấp với full report).

---

## 3. Quyết định đã chốt (qua hỏi đáp)

| Hạng mục | Quyết định |
|---|---|
| Phong cách | **Cosmic** (vũ trụ huyền bí) — navy→đen, starfield, đường nối chòm sao, glow vàng |
| Nền tối | **Điểm nhấn** (cover + trang chia chương + trang biểu đồ tối; trang nội dung dài giữ cream sáng + sao mờ + glow) — ưu tiên đọc hiểu & in được |
| Biểu đồ | **Cả 4**: (1) cột sức mạnh 1-9, (2) radar số cốt lõi, (3) timeline đỉnh cao+thử thách, (4) vòng chu kỳ 9 năm |
| Hình ảnh | **Hybrid**: AI cover+archetype (tái dùng pipeline) + thư viện ornament/sacred-geometry **tĩnh SVG** |
| Phạm vi | **Tất cả report** (overview/love/career + mini/free), free cũng đủ 4 biểu đồ |

---

## 4. Giải pháp đề xuất

### 4.1 Render biểu đồ — inline SVG sinh từ Python (KHÔNG matplotlib)

**Khuyến nghị:** module mới `app/services/report_charts.py` (pure functions, testable, no I/O):
- `power_bar_svg(counts)` — cột tần suất 1-9
- `core_radar_svg(values)` — radar 5-7 trục số cốt lõi
- `peaks_timeline_svg(peaks, challenges, age)` — trục thời gian theo tuổi
- `cycle_wheel_svg(personal_year)` — donut 9 năm, highlight năm hiện tại

Trả về **chuỗi SVG** (radar/wheel cần lượng giác → làm trong Python sạch hơn nhiều so với Jinja), template nhúng qua `|safe`. Giữ palette đồng bộ với `_theme.css`.

**Vì sao không matplotlib:** dep nặng, output raster/SVG cồng kềnh, khó theme navy/gold, chậm hơn. SVG tay = vector sắc nét, file nhỏ, theme hoàn toàn, **đồng nhất với `birth_chart_svg` đang có**. (YAGNI/KISS)

### 4.2 Theme Cosmic dạng điểm nhấn

- `@page` mới: `chapter` (chia chương, nền tối + sao) + `chart` (trang biểu đồ nền tối + glow).
- **Starfield** dùng lại được: 1 SVG/CSS nhẹ (chấm + vài đường chòm sao) → nền trang tối + watermark **rất mờ** trên trang cream.
- **Glow số**: halo vàng quanh `.number-badge` / số tâm điểm biểu đồ.
- Trang nội dung dài: giữ cream, thêm drop-cap (`::first-letter`) + đường kẻ vàng + sao watermark mờ.
- **Motif chòm sao theo số chủ đạo**: pattern chấm trang trí (không cần đúng thiên văn) → tăng "bí hiểm".

### 4.3 Hình ảnh hybrid

- Giữ nguyên cover AI + archetype (đã build, fail-safe, cache theo số).
- Thêm thư viện tĩnh `static/report-assets/ornaments/` — **SVG** (scalable, theme qua `currentColor`): hoa văn góc, sacred geometry (flower/seed of life, metatron), bộ glyph chiêm tinh/giả kim, divider motif. Tạo 1 lần (dùng skill `ai-multimodal`/`imagemagick`).

---

## 5. Rủi ro & giảm thiểu

| Rủi ro | Giảm thiểu |
|---|---|
| **WeasyPrint SVG filter (blur/glow) hỗ trợ hạn chế** | Thử trước; fallback: lớp SVG nhân đôi mờ hoặc `radial-gradient` halo thay vì `filter` |
| **Glyph unicode chiêm tinh (♈⚗) thiếu trong font** | Dùng **SVG ornament** thay vì dựa vào unicode astro |
| Master number 11/22 trên radar/biểu đồ | Cap thang đo hoặc marker riêng |
| Free/mini thiếu dữ liệu đẹp cho radar/timeline | Xác nhận context mini có `peaks/challenges/core`; nếu thiếu → task wiring nhỏ |
| Nền tối tốn mực/nặng file | Đã chọn **điểm nhấn**; starfield SVG nhẹ, ảnh AI đã cap 1240px |
| Đọc text Việt dài | Trang nội dung giữ cream sáng (đã chốt) |

---

## 6. Tiêu chí thành công

- 4 biểu đồ render đúng trong PDF (WeasyPrint), đúng dữ liệu user, theme đồng bộ.
- Cover/chương/biểu đồ cảm giác "cosmic"; trang nội dung vẫn dễ đọc.
- Không tăng đáng kể thời gian render (SVG ~ms) & dung lượng PDF.
- Áp dụng được cho mọi template (đa số work tập trung ở `base_report.html` + `_theme.css` + `_macros.html`).
- Tests cho `report_charts.py` (geometry/SVG output) pass.

---

## 7. Câu hỏi chưa giải quyết (cần xác nhận trước/khi plan)

1. **Template nào đang thực sự được fulfillment dùng cho từng loại report?** Có vẻ song song giữa `invoice.html` (full, dùng `build_report_view` → có `calc`) và `reports/report-*.html` (dùng `content` dict shape khác). Cần xác minh wiring để biết chèn biểu đồ ở đâu & free/mini có `calc` không.
2. Free/mini hiện có truyền `calc`/peaks/challenges vào context PDF chưa? (quyết định có cần task wiring dữ liệu cho bản free).
3. Có cần tạo asset ornament/sacred-geometry mới ngay trong phạm vi này, hay dùng tạm bộ tối thiểu rồi bổ sung sau?

---

## 8. Bước tiếp theo

→ Chạy `/ck:plan` với context này để tạo plan chi tiết: (1) xác minh template wiring, (2) `report_charts.py` + tests, (3) macros + chèn template, (4) theme cosmic (`@page`, starfield, glow), (5) thư viện ornament SVG, (6) áp dụng đa template + render QA.
