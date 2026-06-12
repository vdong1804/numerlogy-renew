# Phase 02 — Free vs Paid Content Map

**Context:** `plan.md` · Phase 01 (builder dùng tập này)
**Priority:** High · **Status:** ⬜ Not started

## Overview
Định nghĩa **một nguồn sự thật** cho: section nào FREE, section nào khóa, và mã `content_code` của mỗi
section để khớp với `product.content_codes`. Phải đồng bộ với bản PDF free (`invoice-free.html`: power + 9-year
cycle) để on-screen và PDF nhất quán (decision #3).

## Key insights
- `product.content_codes` = danh sách **tên bảng content** (dùng bởi fulfillment `_fetch_content_by_codes`), vocab khác với section của /ket-qua report → **không map 1:1 sạch**.
- **Quyết định KISS (v1):** entitlement **coarse** — có order paid (report/combo) khớp identity → mở **toàn bộ** summary sections; không → free. KHÔNG sub-unlock theo từng content_code ở v1 (YAGNI; các product report love/career là báo cáo riêng, không phải mở lẻ section của màn summary). Granular = future enhancement (ghi chú trong code).
- Free tier teaser: số chủ đạo (content chính, ẩn content_2..5) + power chart + chu kỳ cá nhân; khóa phần còn lại.

## Requirements
- Hằng `FREE_CODES: set[str]` ở backend (vị trí: `report_entitlement_service.py` hoặc `_content_codes.py`).
- Bảng ánh xạ `SECTION_CODE` cho từng section của report:
  - `so_chu_dao`, `core.su_menh|linh_hon|nhan_cach|thai_do|truong_thanh|ngay_sinh|noi_cam`,
    `peaks`, `challenges`, `personal.nam|thang`, `karmic`, `missing`, `power_chart`.
- Đề xuất FREE (chốt với user nếu cần): `so_chu_dao` (content chính, ẩn content_2..5), `power_chart`, `personal.*`.
- Khóa: toàn bộ 7 core full, peaks, challenges, karmic, missing, và content_2..5 của số chủ đạo.

## Architecture
```
SECTION_CODE (section → code)  ──┐
                                 ├─► build_report._gate()  (Phase 01)
product.content_codes (DB)  ─────┘   unlocked = FREE_CODES ∪ purchased codes
invoice-free.html (power+cycle) ─── giữ đồng bộ với FREE_CODES
```

## Related code files
**Inspect/Modify**
- `numerology-api/scripts/_content_codes.py` — xem danh mục code hiện có; bổ sung nếu thiếu.
- `numerology-api/app/services/report_entitlement_service.py` — `FREE_CODES` + `SECTION_CODE` (hoặc import từ `_content_codes`).
**Cross-check**
- Product seed/migration: `numerology-api/scripts/data/`, `alembic/versions/*` — đảm bảo product `content_codes` dùng đúng vocab.
- `app/templates/reports/invoice-free.html` — chart free khớp `FREE_CODES`.

## Implementation steps
1. Đọc `_content_codes.py` + product seed để lấy vocab code hiện hành; lập bảng đối chiếu section↔code.
2. Chốt `FREE_CODES` (đề xuất ở trên) — nếu lệch với product hiện có, ghi chú điều chỉnh.
3. Khai báo `SECTION_CODE` + `FREE_CODES`; export cho Phase 01.
4. Verify product `content_codes` của các gói report bao phủ đúng section khóa (không có code "mồ côi").
5. Đối chiếu `invoice-free.html` để on-screen free == PDF free.

## Todo
- [ ] Đọc `_content_codes.py` + product seed
- [ ] Bảng section→code
- [ ] `FREE_CODES` chốt
- [ ] Verify product content_codes coverage
- [ ] Đồng bộ invoice-free

## Success criteria
- Mỗi section report map tới đúng 1 code; `FREE_CODES` khớp invoice-free.
- Mua gói X → đúng các section X mở trên /ket-qua.

## Risks
- Vocab code phân mảnh giữa script/seed/template → cần một bảng chuẩn, tránh tạo vocab thứ hai.

## Next
→ Phase 03 FE render theo `locked` flag.
