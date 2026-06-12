# Phase 05 — Tests

**Priority:** P2 · **Status:** pending · **Depends:** P1–P4
**Files:** `numerology-api/tests/test_numerology_chart.py` (mới), `tests/test_numerology_full_report.py` (mới/mở rộng)

## Môi trường (theo memory)
- Tests chạy TRONG docker container `numerology-api-api-1`.
- Prod image thiếu pytest → `docker exec numerology-api-api-1 pip install pytest pytest-asyncio httpx aiosqlite respx` trước.
- Code bind-mount `.:/app` → sửa host áp dụng live.
- **4 integration fail có sẵn** (`test_numerology_endpoints.py`: phone 422, la-so 400/422) — KHÔNG liên quan, không fix ở đây.

## Unit — `test_numerology_chart.py` (pure, không DB)
- `compute_arrows`: DOB toàn {1,4,7} → present chứa "147"; thiếu hẳn {2,5,8} → empty chứa "not_258"; line "123" trống → KHÔNG xuất hiện (NOT_AVAILABLE).
- `compute_isolated`: 1 có mặt, thiếu 2/4/5 → [1]; 1 có mặt nhưng có 4 → [].
- `detect_karmic_debt`: 13→13, 14→14, 16→16, 19→19, 22→None, 12→None.
- `compound_str(13,4)` == "13/4".

## Unit — calc (`calculate_numerology_numbers`)
- Sinh ngày 13 (vd "13011990") → `no_nghiep` chứa 13.
- Dict có đủ key mới: `so_nam_ca_nhan, so_chu_dao_compound, no_nghiep, arrows_present, arrows_empty, isolated, name_counts`.
- `so_nam_ca_nhan` ∈ 1..9.

## Integration — `build_report_view` (cần DB seeded)
- Gọi `build_report_view(db, name, dob_with_debt, phone)` → `sections` có heading chứa "SỐ NỢ NGHIỆP", "SỐ NĂM CÁ NHÂN".
- `chart_grid_name`, `chart_grid_combined`, `name_chart_sections` không rỗng.
- DOB không nợ nghiệp → không có section "SỐ NỢ NGHIỆP".

## Integration — JSON `build_report`
- Field `karmic_debt`, `personal.nam_ca_nhan`, `name_chart`, `arrows`, `so_chu_dao.compound` tồn tại.

## Todo
- [ ] Viết test_numerology_chart.py (unit thuần).
- [ ] Mở rộng/viết test calc cho key mới.
- [ ] Integration test builder (dùng fixture DB hiện có trong conftest).
- [ ] `docker exec numerology-api-api-1 python -m pytest tests/test_numerology_chart.py tests/test_numerology_full_report.py -v`.
- [ ] Toàn bộ test mới PASS; 4 fail cũ giữ nguyên (không tăng).

## Success criteria
- 100% test mới xanh.
- Không hồi quy test đang xanh.

## Câu hỏi mở
- DOB mẫu chuẩn cho mỗi mã nợ nghiệp 14/16/19 (ngoài 13) — chọn cố định để test ổn định.
