---
phase: 3
title: Static Image Library
status: completed
priority: P2
effort: 1d
dependencies:
  - 2
---

# Phase 3: Static Image Library

## Context Links
- Design doc: `plans/reports/brainstorm-260611-0728-redesign-numerology-report.md`
- Skill: `ai-multimodal` (gen ảnh Imagen 4 / Nano Banana)

## Overview
Gen **1 lần** bộ ảnh tĩnh dùng chung mọi báo cáo: 11 archetype theo Số chủ đạo (1-9, 11, 22), 3-4 divider/ornament, 1 bìa fallback. Lưu vào static, tích hợp vào slot template đã chừa ở P2. **AI chỉ gen nghệ thuật trừu tượng — KHÔNG render chữ.**

## Key Insights
- Cùng Số chủ đạo → cùng archetype → ảnh **tĩnh dùng lại**, không gen per-report (DRY, tiết kiệm).
- Imagen/Gemini render chữ (đặc biệt tiếng Việt) sai dấu → AI chỉ gen art; mọi text overlay bằng CSS (P2/P4).
- Bộ ảnh ~15-18 tấm, chi phí 1 lần vài $.

## Requirements
- Functional: mỗi Số chủ đạo (1,2,3,4,5,6,7,8,9,11,22) có 1 ảnh archetype; có divider + bìa fallback; template hiển thị đúng ảnh theo `calc["so_chu_dao"]`.
- Non-functional: ảnh tối ưu dung lượng (web/PDF), phong cách nhất quán (cùng prompt style navy+gold huyền bí), kích thước/tỉ lệ chuẩn cho slot.

## Architecture
- Thư mục: `static/report-assets/archetypes/{N}.webp` (N ∈ 1-9,11,22), `static/report-assets/dividers/*.svg|webp`, `static/report-assets/cover-fallback.webp`.
- Prompt style guide (lưu kèm để tái tạo nhất quán): chủ đề tâm linh/thiên văn, palette navy #002060 + gold #C9A227, no text, no human faces cụ thể (tránh lệ thuộc), tỉ lệ cố định.
- Tích hợp template: macro/biến map `so_chu_dao → archetype path`; section "Số chủ đạo" render `<img>` archetype; divider dùng ở section breaks; bìa fallback dùng khi P4 chưa/không có bìa per-user.
- Helper resolve path: hàm nhỏ (vd trong `numerology_full_report.py` hoặc util mới) trả `archetype_image` vào report dict để template tham chiếu — giữ template "ngu", logic ở Python.

## Related Code Files
- Create: `static/report-assets/archetypes/*`, `static/report-assets/dividers/*`, `static/report-assets/cover-fallback.webp`, style-guide note (vd `static/report-assets/PROMPTS.md`).
- Create (nếu cần): `app/services/report_assets.py` — map số → đường dẫn ảnh (KISS).
- Modify: `app/services/numerology_full_report.py` — thêm `archetype_image` vào dict trả về; `app/templates/invoice.html`, `invoice-free.html`, `reports/*` — fill slot ảnh.

## Implementation Steps
1. Viết style-guide prompt (palette, mood, no-text, tỉ lệ). Quyết Imagen 4 vs Nano Banana sau test 1-2 ảnh mẫu.
2. Gen 11 archetype qua `ai-multimodal` skill; review nhất quán; regen tấm lệch.
3. Gen/derive 3-4 divider + 1 bìa fallback.
4. Optimize (resize/webp) + lưu `static/report-assets/...`.
5. Viết `report_assets.py` map số → path; thêm `archetype_image` vào report dict.
6. Fill slot trong template (cả 2 họ); đảm bảo `base_url` cho `<img>` local (WeasyPrint).
7. Render verify qua Docker: ảnh hiện đúng theo số chủ đạo, không vỡ layout, dung lượng PDF chấp nhận được.

## Todo List
- [ ] Style-guide prompt + chọn model (Imagen4/Nano Banana)
- [ ] Gen 11 archetype + review nhất quán
- [ ] Gen divider + bìa fallback
- [ ] Optimize + lưu `static/report-assets/`
- [ ] `report_assets.py` map số → path
- [ ] Fill slot template (2 họ) + base_url cho img
- [ ] Render verify qua Docker

## Success Criteria
- [ ] 11 archetype + divider + bìa fallback tồn tại, phong cách nhất quán.
- [ ] Báo cáo hiển thị đúng archetype theo `so_chu_dao`.
- [ ] Không ảnh nào chứa chữ AI; mọi text là CSS overlay/markup.
- [ ] Dung lượng PDF không tăng quá mức (ảnh đã optimize).

## Risk Assessment
- **Ảnh không nhất quán style** giữa các số: → cùng prompt skeleton + seed/style ref; regen tấm lệch.
- **Master number (11/22) edge**: → đảm bảo map có key 11,22; fallback divider nếu thiếu.
- **PDF phình to vì ảnh**: → webp + resize hợp tỉ lệ in.
- **base_url ảnh local sai** → ảnh không hiện: → test trong Docker, path tương đối chuẩn.

## Security Considerations
- Ảnh tĩnh local — không fetch remote lúc render (giảm SSRF). Nếu dùng `<img src>` local, không cho URL ngoài.

## Next Steps
- P4 thêm bìa per-user, dùng `cover-fallback.webp` làm fallback.
