# Phase 01 — Chart engine (`report_charts.py`) + tests

**Priority:** High · **Status:** ✅ complete · **Depends:** —

## Overview
Module thuần (pure, no I/O) sinh 4 biểu đồ dạng **inline SVG string**, theme đồng bộ `_theme.css` (navy #002060, gold #c9a227, vermilion #b0392b, cream #fbf8f0). Foundation cho mọi phase sau. KHÔNG matplotlib.

## Key insights
- Dữ liệu lấy từ `calc` dict (`calculate_numerology_numbers`). Không chạm DB.
- Radar/wheel cần lượng giác → làm trong Python (sạch hơn Jinja nhiều).
- Đồng nhất pattern với `m.birth_chart_svg` đang có (viewBox + `<text>`).

## Related code files
- **Create:** `numerology-api/app/services/report_charts.py`
- **Create:** `numerology-api/tests/services/test_report_charts.py`
- **Reference:** `app/core/numerology.py`, `app/core/numerology_chart.py` (keys của calc), `app/templates/reports/_macros.html` (style birth_chart_svg), `app/services/numerology_report_builder.py` (`_digit_counts`).

## API (functions)
```python
def power_bar_svg(counts: dict[str, int]) -> str        # cột tần suất số 1..9
def core_radar_svg(values: dict[str, int]) -> str       # radar 5-7 trục, label→value
def peaks_timeline_svg(peaks: list[dict]) -> str        # [{stage, age_start, peak, challenge}]
def cycle_wheel_svg(personal_year: int) -> str          # donut 9 năm, highlight năm hiện tại
def build_charts(calc: dict) -> dict[str, str]          # gom 4 svg từ calc → {"power","radar","timeline","wheel"}
```

## Implementation steps
1. Hằng palette ở đầu module (đồng bộ `_theme.css`).
2. `power_bar_svg`: trục x = 1..9, cao cột tỉ lệ count, max-scale theo max(counts) (min 1 tránh chia 0). Nhãn số dưới chân, value trên đỉnh. viewBox cố định (vd 0 0 360 200).
3. `core_radar_svg`: input label→value cho ~6 trục (Chủ đạo, Sứ mệnh, Linh hồn, Nhân cách, Thái độ, Trưởng thành). Chuẩn hoá: master 11/22 → cap về thang 1-9 cho bán kính (giữ nhãn hiển thị số gốc). Vẽ lưới đa giác + polygon dữ liệu (fill gold mờ, stroke gold), nhãn quanh đỉnh.
4. `peaks_timeline_svg`: 4 mốc theo `age_start` tăng dần, đường ngang + node tròn (số đỉnh cao trong node, số thử thách nhãn phụ), nhãn tuổi dưới.
5. `cycle_wheel_svg`: donut 9 cung đều, cung = `personal_year` highlight (fill gold + glow radial), số 1..9 trên từng cung.
6. `build_charts(calc)`: dựng input cho từng hàm từ key calc:
   - power: `{str(d): birth_day_digits + name_digits}` — tái dùng quy ước `_digit_counts` (đếm trên `calc["text_name"]` + ngày sinh). Lưu ý: build_charts chỉ nhận `calc`; nếu cần ngày sinh thô, đọc từ calc (kiểm tra key) hoặc đổi chữ ký thành `build_charts(calc, birth_day)`.
   - radar: 6 số cốt lõi từ `calc["so_*"]`.
   - timeline: `[{stage:i, age_start:calc[f"tuoi_dinh_cao_{i}"], peak:calc[f"dinh_cao_{i}"], challenge:calc[f"thu_thach_{i}"]} for i in 1..4]`.
   - wheel: `calc["so_nam_ca_nhan"]`.
7. Mọi SVG: `width/height` bỏ trống, dùng class CSS (`.chart-svg`, mới: `.chart-bar/.chart-radar/...`) để theme phase sau control kích thước.

## Edge cases
- counts toàn 0 (tên/ngày không có số đó) → vẫn vẽ trục, cột 0.
- master number 11/22/33 trong radar → cap bán kính ≤9, nhãn giữ "11".
- `so_nam_ca_nhan` ngoài 1-9 (lý thuyết không) → clamp.
- build_charts thiếu key → trả svg rỗng/None cho chart đó (caller guard).

## Todo
- [ ] Tạo `report_charts.py` với 5 hàm
- [ ] Palette consts đồng bộ theme
- [ ] Xử lý master number + chia-0
- [ ] `test_report_charts.py`: snapshot/contains assertions (mỗi hàm trả `<svg`, chứa số đúng, không lỗi với input biên)
- [ ] Chạy `pytest tests/services/test_report_charts.py`

## Success criteria
- 5 hàm trả SVG hợp lệ; tests pass; pure (không import DB/async); file ≤200 dòng (tách helper nếu vượt).

## Risks
- Lượng giác radar/wheel sai vị trí → test bằng kiểm tra toạ độ điểm mốc.
- Chữ ký `build_charts` cần birth_day: quyết định ở step 6 (ưu tiên `build_charts(calc, birth_day)` cho rõ ràng).
