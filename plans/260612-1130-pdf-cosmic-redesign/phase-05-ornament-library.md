# Phase 05 — Thư viện ornament SVG (hybrid imagery)

**Priority:** Medium · **Status:** ✅ complete · **Depends:** 04

## Overview
Bổ sung hình ảnh trang trí **tĩnh SVG** (sacred geometry, hoa văn góc, divider motif, constellation theo số) — phần "static" của chiến lược hybrid. Giữ nguyên cover AI + archetype đã có.

## Key insights
- SVG > raster: scalable, nhẹ, theme qua `currentColor`/fill, không phụ thuộc font.
- Tái dùng pattern `report_assets.py` (path helper, trả None nếu thiếu → template degrade).
- Tạo asset 1 lần (dùng skill `ck:ai-multimodal` / `ck:imagemagick`, hoặc SVG path thủ công cho hình học).

## Related code files
- **Create:** `static/report-assets/ornaments/*.svg` (flower-of-life, seed-of-life, corner-flourish, divider-motif, constellation-{1..9,11,22}.svg)
- **Modify:** `app/services/report_assets.py` (thêm `ornament(name) -> str|None`)
- **Modify:** `_theme.css` + templates (dùng ornament làm watermark/divider/góc)
- **Reference:** `cover_generator.py`, `report_assets.py` (pattern hiện có)

## Implementation steps
1. `report_assets.ornament(name)`: trả path tương đối nếu file tồn tại, else None (giống `archetype_image`).
2. Tạo bộ tối thiểu trước (YAGNI): `sacred-geometry-watermark.svg` (flower/seed of life) + `divider-motif.svg` + `corner-flourish.svg`. Constellation-by-number để sau nếu cần.
3. Watermark sacred geometry: nền mờ giữa trang chương (opacity rất thấp, gold/navy).
4. Divider motif: nâng cấp `m.divider()` (tùy chọn dùng SVG thay ký tự ◆).
5. Constellation theo số chủ đạo (nếu làm): map số → file; chèn ở chapter divider cạnh số lớn.
6. Tất cả tham chiếu phải guard `{% if ... %}` (None → bỏ qua).

## Edge cases
- Asset thiếu → None → template không vỡ.
- currentColor: đảm bảo SVG dùng `fill="currentColor"` để ăn theo màu context (sáng/tối).

## Todo
- [ ] `ornament()` helper + test path
- [ ] Tạo 3 SVG tối thiểu (watermark, divider, corner)
- [ ] Áp watermark vào chapter; divider motif vào `m.divider`
- [ ] (Optional) constellation-by-number
- [ ] Render kiểm hình hiển thị đúng, không vỡ

## Success criteria
- Hoa văn hiển thị tinh tế, đồng bộ cosmic; thiếu asset vẫn an toàn; không tăng dung lượng đáng kể.

## Risks
- WeasyPrint render SVG external: dùng `<img src>` path tương đối (base_url=project root) — đã hoạt động với archetype. Inline `<svg>` cũng OK.
- Đừng lạm dụng → rối mắt; giữ tối giản (KISS).
