# Phase 04 — Template + Frontend

**Priority:** P2 · **Status:** pending · **Depends:** P2, P3
**Files:** `app/templates/invoice.html` (sửa), `Numerology-Landing-Page/src/models/numerology-report.ts` (sửa), `src/pages/ket-qua/index.tsx` (sửa)

## A. invoice.html (báo cáo dài PDF/web)
Hiện trạng: dòng 46 `m.birth_chart_svg(report.chart_grid)`, dòng 47 lặp `chart_sections`, dòng 54 lặp `sections`.
- **Mục text mới** (Nợ Nghiệp, Năm Cá Nhân) **tự render** qua vòng `sections` — không cần sửa.
- **Mũi tên + lẻ loi** đã nối vào `chart_sections` (P2) → tự render.
- **Biểu Đồ Tên + Tổng Hợp (G3):** thêm sau khối biểu đồ ngày sinh:
```jinja
<h3>BIỂU ĐỒ TÊN</h3>
{{ m.birth_chart_svg(report.chart_grid_name) }}
{% for sec in report.name_chart_sections %}
  <h4>{{ sec.heading }}</h4>{{ sec.content|safe }}
{% endfor %}
<h3>BIỂU ĐỒ TỔNG HỢP TÊN & NGÀY SINH</h3>
{{ m.birth_chart_svg(report.chart_grid_combined) }}
```
- Tái dùng macro `birth_chart_svg` (cùng layout 3×3). Kiểm tra macro chấp nhận grid số 0 (ô trống).

## B. Frontend landing (`ket-qua`)
- `models/numerology-report.ts`: thêm type cho `karmic_debt[]`, `personal.nam_ca_nhan`, `name_chart[]`, `arrows{present,empty,isolated}`, `so_chu_dao.compound`, `power_chart.combined`.
- `ket-qua/index.tsx`: render block mới:
  - Nợ Nghiệp (chỉ khi `karmic_debt.length`).
  - Năm Cá Nhân.
  - Biểu đồ tên / tổng hợp (nếu landing có UI biểu đồ — nếu không, hiển thị count đơn giản).
  - Mũi tên mạnh/trống (badge từ `arrows`).
  - Chủ Đạo hiển thị `compound`.

## Todo
- [ ] invoice.html: 2 khối chart mới + headings.
- [ ] Verify `birth_chart_svg` render ô 0 (không lỗi).
- [ ] TS types mở rộng (không phá build `tsc`).
- [ ] `ket-qua` render field mới, ẩn khi rỗng.
- [ ] Build landing (`npm run build`) pass.

## Success criteria
- PDF/web có biểu đồ tên + tổng hợp + mũi tên + nợ nghiệp + năm cá nhân.
- Landing hiển thị các mục mới, không vỡ layout khi dữ liệu rỗng.

## Rủi ro
- Macro `birth_chart_svg` có thể hardcode nhãn ngày sinh → đọc macro trước khi tái dùng cho tên/tổng hợp; nếu cứng, tổng quát hóa tham số.
