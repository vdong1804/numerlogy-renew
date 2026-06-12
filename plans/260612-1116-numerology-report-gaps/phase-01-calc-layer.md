# Phase 01 — Calc Layer

**Priority:** P0 (chặn P2/P3) · **Status:** pending
**Files:** `app/core/numerology.py` (sửa), `app/core/numerology_chart.py` (mới ~80 dòng)

## Mục tiêu
`calculate_numerology_numbers()` trả thêm các trường cho G1–G6. Tách logic biểu đồ sang module mới (numerology.py đang 176 dòng, tránh vượt 200).

## Module mới: `app/core/numerology_chart.py`
8 mũi tên Pytago (layout 3-6-9 / 2-5-8 / 1-4-7):
```
LINES = ["147","258","369","123","456","789","159","357"]   # 3 hàng, 3 cột, 2 chéo
# not_123 sẽ được seed ở P6 → KHÔNG cần guard NOT_AVAILABLE. Phát đủ 8 mũi tên trống.
NEIGHBORS = {1:{2,4,5}, 3:{2,5,6}, 7:{4,5,8}, 9:{5,6,8}}     # ô kề số góc
KARMIC = {13,14,16,19}
```
Hàm:
- `compute_arrows(present: set[str]) -> tuple[list[str], list[str]]`
  - mạnh: line mà cả 3 chữ số đều có trong `present` → code `"147"`.
  - trống: line mà cả 3 chữ số đều VẮNG → code `"not_147"` (đủ 8 line, kể cả `not_123`).
- `compute_isolated(present: set[str]) -> list[int]`
  - với d ∈ {1,3,7,9}: nếu `str(d) in present` và `NEIGHBORS[d]` không giao `present` → thêm d. (số lẻ loi → fetch `{d}_single`).
- `detect_karmic_debt(total: int) -> int | None`
  - rút `total` xuống còn ≤2 chữ số; trả về giá trị 2-chữ-số nếu ∈ KARMIC, ngược lại None. (Dùng cho 5 cốt lõi.)
- `compound_str(total: int, reduced: int) -> str` → `f"{total}/{reduced}"` (vd "13/4", "22/4").

## Sửa `numerology.py`
1. **Năm Cá Nhân (G2):** đổi `_so_nam_ca_nhan` → `so_nam_ca_nhan` (giữ công thức cũ `get_sum(get_sum(now.year)+so_thai_do) or 9`, dạng đơn 1-9). Tháng Cá Nhân vẫn dùng biến này. Thêm `so_nam_ca_nhan` vào dict return.
2. **Nợ Nghiệp (G1):** thu thập tổng-trước-rút-gọn của 5 cốt lõi, áp `detect_karmic_debt`, kết quả **sort tăng dần**:
   - Chủ Đạo: total = `day_sum+month_sum+year_sum` (đã có) → `detect_karmic_debt`.
   - Ngày Sinh: `int(birth_day[0:2])` (ngày trong tháng, 1-31) → 13/14/16/19 → debt.
   - Sứ Mệnh: `sum_full_name`; Linh Hồn: `sum_full_vowel`; Nhân Cách: `sum_full_consonant`.
   - `no_nghiep = sorted({d for d in map(detect_karmic_debt, [...]) if d})`. Thêm vào dict.
3. **Compound (G6):** `so_chu_dao_compound = compound_str(two_digit_chu_dao, get_sum(so_chu_dao))` — `two_digit` = rút `day_sum+month_sum+year_sum` xuống ≤2 chữ số. Thêm vào dict.
4. **Mũi tên + lẻ loi (G4/G5):** `present = {c for c in birth_day if c in '123456789'}`; `arrows_present, arrows_empty = compute_arrows(present)`; `isolated = compute_isolated(present)`. Thêm cả 3 vào dict.
5. **Biểu đồ tên (G3):** `name_counts = {str(d): text_name.count(str(d)) for d in range(1,10)}`. Thêm vào dict (builder dựng lưới + combined).

## Todo
- [ ] Tạo `numerology_chart.py` + 4 hàm + hằng số, có comment.
- [ ] Wire 5 nhóm trường vào dict return của calc.
- [ ] `from app.core.numerology_chart import ...` ở đầu numerology.py.
- [ ] Chạy `python -c "from app.core.numerology import calculate_numerology_numbers as f; print(f('13101990','Nguyen Van A'))"` (host hoặc docker) — không lỗi, có đủ key mới.

## Success criteria
- DOB sinh ngày 13/14/16/19 → `no_nghiep` chứa mã tương ứng.
- DOB toàn 1,4,7 → `arrows_present` chứa "147".
- Số 1 không kèm 2/4/5 → `isolated` chứa 1.
- `so_nam_ca_nhan`, `so_chu_dao_compound`, `name_counts` xuất hiện trong dict.

## Rủi ro
- `detect_karmic_debt` phải rút đúng tới bước 2-chữ-số (vd 13 không tự rút thành 4 trước khi check). Viết vòng `while total>9 ... ` nhưng check KARMIC ở mức ≤19 trước khi rút tiếp.
