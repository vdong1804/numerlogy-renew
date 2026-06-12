# Phase 02 — Full Report Builder (PDF/web dài)

**Priority:** P1 · **Status:** pending · **Depends:** P1
**Files:** `app/services/numerology_full_report.py` (sửa), `app/services/numerology_db.py` (sửa nếu cần)

## Mục tiêu
`build_report_view()` render đủ mục mới đúng thứ tự MỤC LỤC, dùng nội dung DB đã có.

## Sửa `numerology_full_report.py`
Imports thêm: `KarmicDebtNumber, PersonalYearNumber, NameChart`.

### 1. Số Nợ Nghiệp (G1) — chèn SAU Số Nội Cảm, TRƯỚC Số Thiếu
```python
for code in calc["no_nghiep"]:
    await add(f"SỐ NỢ NGHIỆP {code}/{get_sum(code)}", KarmicDebtNumber, code)
```
(không có → bỏ qua, list rỗng.)

### 2. Số Năm Cá Nhân (G2) — SAU Số Điện Thoại, TRƯỚC Tháng Cá Nhân
```python
await add(f"SỐ NĂM CÁ NHÂN {calc['so_nam_ca_nhan']}", PersonalYearNumber, calc["so_nam_ca_nhan"])
```

### 3. Biểu Đồ Tên + Tổng Hợp (G3)
- `name_counts = calc["name_counts"]`.
- `chart_grid_name = [[(int(d)*name_counts[d]) for d in r] for r in _CHART_LAYOUT]`.
- `chart_grid_combined`: ô = chuỗi/đếm gộp ngày sinh + tên (hiển thị tổng số lần xuất hiện ở mỗi ô; thống nhất kiểu với chart_grid hiện tại).
- `name_chart_sections`: với mỗi digit có mặt trong tên → `await row(NameChart, d)` → list {heading:f"Số {d} trong biểu đồ tên", content}.
- Thêm `chart_grid_name`, `chart_grid_combined`, `name_chart_sections` vào dict return.

### 4. Mũi tên + lẻ loi (G4/G5) — nối vào `chart_sections`
```python
for code in calc["arrows_present"]:
    r = await row(BirthdayChart, code)
    if r: chart_sections.append({"heading": r.title or f"Mũi tên {code}", "content": r.content})
for code in calc["arrows_empty"]:
    r = await row(BirthdayChart, code)            # code đã có tiền tố not_
    if r: chart_sections.append({"heading": r.title or f"Mũi tên trống {code}", "content": r.content})
for d in calc["isolated"]:
    r = await row(BirthdayChart, f"{d}_single")
    if r: chart_sections.append({"heading": r.title or f"Số {d} lẻ loi", "content": r.content})
```

### 5. Hiển thị kép (G6)
- Heading Số Chủ Đạo: `f"SỐ CHỦ ĐẠO {calc['so_chu_dao_compound']}"`.
- `summary`: dòng "Số chủ đạo" dùng `calc['so_chu_dao_compound']`; thêm dòng "Số nợ nghiệp" = `", ".join(f"{c}/{get_sum(c)}" for c in calc['no_nghiep']) or "—"`, "Số năm cá nhân" = `calc['so_nam_ca_nhan']`.

## Todo
- [ ] Thêm imports + 5 khối trên đúng thứ tự TOC.
- [ ] Mở rộng dict return (chart_grid_name, chart_grid_combined, name_chart_sections).
- [ ] Cập nhật `summary` (compound chủ đạo + nợ nghiệp + năm cá nhân).
- [ ] Render thử qua `GET /api/?...` (numerology_free debug HTML) — không lỗi, có mục mới.

## Success criteria
- Báo cáo có section "SỐ NỢ NGHIỆP …" (khi có), "SỐ NĂM CÁ NHÂN …", mũi tên, lẻ loi, biểu đồ tên/tổng hợp.
- Chủ Đạo hiển thị dạng kép.
- Người không có nợ nghiệp → không phát sinh section rỗng.

## Note
`numerology_db.py::get_numerology_models` phục vụ JSON builder (P3) — KHÔNG cần đổi cho P2 (P2 fetch trực tiếp qua `row()`).
