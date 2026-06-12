# Phase 03 — JSON Summary Builder (landing)

**Priority:** P1 · **Status:** pending · **Depends:** P1 (song song P2)
**Files:** `app/services/numerology_report_builder.py` (sửa), `app/services/numerology_db.py` (sửa)

## Mục tiêu
JSON `build_report()` (màn `ket-qua`) expose các trường mới để đồng bộ với báo cáo dài.

## Sửa `numerology_db.py::get_numerology_models`
Thêm fetch (dùng cho JSON builder):
```python
'karmic_debt': await fetch_many_by_codes(db, KarmicDebtNumber, calc['no_nghiep']),
'personal_year_number': await fetch_by_code(db, PersonalYearNumber, calc['so_nam_ca_nhan']),
'name_chart': await fetch_many_by_codes(db, NameChart, [str(d) for d in range(1,10) if calc['name_counts'][str(d)]]),
```
Imports thêm: `KarmicDebtNumber, PersonalYearNumber, NameChart`.

## Sửa `numerology_report_builder.py::build_report`
Thêm vào dict return:
- `"so_chu_dao"`: thêm field `"compound": calc["so_chu_dao_compound"]`.
- `"karmic_debt"`: `[{"code": r.code, "title": r.title, "content": r.content} for r in models.get("karmic_debt") or []]`.
- `"personal"`: thêm `"nam_ca_nhan": _row(models.get("personal_year_number"), calc["so_nam_ca_nhan"])`.
- `"name_chart"`: `[_row(r, r.code) for r in (models.get("name_chart") or [])]`.
- `"arrows"`: `{"present": calc["arrows_present"], "empty": calc["arrows_empty"], "isolated": calc["isolated"]}`.
- `"power_chart"`: giữ `birth` + `name`; thêm `"combined"` = cộng đếm birth+name mỗi chữ số (đồng bộ G3).

## Todo
- [ ] Mở rộng `get_numerology_models` (3 fetch + imports).
- [ ] Mở rộng `build_report` (5 nhóm field).
- [ ] Xác nhận `calc` truyền vào builder đã có key mới (từ P1).
- [ ] Gọi thử `GET /api/numerology-report` → JSON có field mới.

## Success criteria
- JSON chứa `karmic_debt`, `personal.nam_ca_nhan`, `name_chart`, `arrows`, `so_chu_dao.compound`, `power_chart.combined`.
- Người không nợ nghiệp → `karmic_debt: []`.

## Note
`build_report` là hàm pure (calc + models). Mọi DB fetch nằm ở `get_numerology_models` — giữ ranh giới này.
