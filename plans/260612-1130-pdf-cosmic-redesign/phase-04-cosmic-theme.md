# Phase 04 — Cosmic theme (điểm nhấn): @page, starfield, glow

**Priority:** High · **Status:** ✅ complete · **Depends:** —  (song song được với 01-03)

## Overview
Nâng thẩm mỹ theme sang **vũ trụ huyền bí dạng điểm nhấn**: cover + trang chia chương + trang biểu đồ nền tối (navy→đen + sao + glow vàng); trang nội dung dài giữ **cream sáng** + sao watermark mờ. Ưu tiên đọc hiểu + in được.

## Key insights
- `_theme.css` inline vào mọi template (base_report + invoice*) → sửa 1 chỗ, phủ toàn bộ.
- WeasyPrint: `@page` named, `background` gradient/SVG, `::first-letter`, radial-gradient OK. **`filter: blur` hỗ trợ kém → glow dùng `radial-gradient`/layered, KHÔNG filter.**
- Hiện đã có `@page cover` (dark). Mở rộng thêm `chapter`/`chart`.

## Related code files
- **Modify:** `app/templates/reports/_theme.css` (chính)
- **Modify:** `app/templates/reports/base_report.html` (class trang chương + starfield markup nếu cần)
- **Modify:** `app/templates/invoice.html` (áp class chương/chart cho section tương ứng)
- **Reference:** `_fonts.css` (Playfair/Lora)

## Implementation steps
1. **Named pages**:
   - `@page chart { background: radial-gradient(...) navy→#001026; @top/@bottom giữ tối-vàng }` cho trang biểu đồ.
   - `@page chapter { ... }` cho trang mở chương (số lớn + glow + constellation).
   - Trang nội dung: giữ `@page` mặc định (cream) — thêm watermark sao **rất mờ** (background-image SVG data-uri, opacity thấp).
2. **Starfield**: 1 SVG nhỏ (chấm trắng/vàng rải + vài đường nối chòm sao) → dùng làm `background` cho `.chart-page`/`.chapter` (tối) và watermark mờ trang cream. Lưu `static/report-assets/cosmic/starfield.svg` (hoặc inline data-uri trong CSS để tránh phụ thuộc path).
3. **Glow số**: `.number-badge`, số tâm chart → bọc `radial-gradient(circle, rgba(201,162,39,.55), transparent 70%)` làm lớp nền tròn phía sau (KHÔNG filter blur). Thêm `.glow` utility class.
4. **Drop-cap**: `.content > p:first-of-type::first-letter` (Playfair, gold, lớn) cho đoạn mở chương.
5. **Chapter divider**: class `.chapter` cho section mở mỗi nhóm lớn (vd "SỐ CHỦ ĐẠO") — nền tối, số lớn glow, constellation motif, archetype image. Áp ở invoice.html section `loop.first` & base_report nếu phù hợp.
6. **Chart page styling**: `.chart-page` nền tối → chỉnh màu chữ/đường chart (Phase 01 SVG dùng currentColor hoặc class để đảo màu trên nền tối: sao, lưới sáng mờ, polygon gold). Đồng bộ palette.
7. Kích thước chart qua CSS: `.chart-bar/.chart-radar/.chart-timeline/.chart-wheel { width: ...mm }`.

## Edge cases
- In trắng đen: nền tối chỉ ở cover/chương/chart (ít trang) → chấp nhận; nội dung chính cream.
- Dung lượng: starfield SVG nhẹ, không raster lớn.

## Todo
- [ ] @page chart + chapter
- [ ] starfield.svg + áp background dark pages + watermark cream
- [ ] glow radial-gradient cho number-badge + chart focal
- [ ] drop-cap ::first-letter
- [ ] chapter divider style + áp template
- [ ] chart-page dark styling đồng bộ SVG

## Success criteria
- Cover/chương/chart "cosmic"; nội dung dễ đọc; không dùng `filter: blur`; render WeasyPrint không cảnh báo nghiêm trọng.

## Risks
- radial-gradient nhiều lớp có thể nặng render → đo ở Phase 06.
- Đảo màu SVG trên nền tối: phối hợp Phase 01 (dùng class/currentColor) — nếu phức tạp, cho chart nền sáng (panel cream) trên trang tối.
