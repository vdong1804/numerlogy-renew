# GAP Analysis — Báo cáo thực tế `SAMPLE 00.00.2000.docx` vs Hệ thống

**Ngày:** 2026-06-12 · **Nguồn chuẩn:** `SAMPLE 00.00.2000.docx` (514 đoạn, 7 bảng, MỤC LỤC 19 mục)
**Builder hệ thống:** `numerology-api/app/services/numerology_full_report.py` (`build_report_view` — single source of truth báo cáo dài) + `numerology_report_builder.py` (JSON tóm tắt landing).
**Tính toán:** `app/core/numerology.py::calculate_numerology_numbers`.

## Đối chiếu MỤC LỤC (19 mục) → trạng thái builder

| # | Mục báo cáo chuẩn | Hệ thống | Trạng thái |
|---|---|---|---|
| 1 | Vài nét về Pytago (static) | n/a (tĩnh) | — |
| 2 | Số Chủ Đạo – Đường Đời | MainNumber | ✅ |
| 3 | Biểu Đồ Ngày Sinh | chart_grid + BirthdayChart/digit | ⚠️ thiếu phần absent-digit + mũi tên |
| 4 | 3 Giai Đoạn Cuộc Đời | StagesOfLife 1-3 | ✅ |
| 5 | 4 Đỉnh Cao Cuộc Đời | LifePeak + ChallengeLife | ✅ |
| 6 | Số Thái Độ | AttitudeNumber | ✅ |
| 7 | Số Ngày Sinh | BirthdayNumber | ✅ |
| 8 | Số Sứ Mệnh | MissionNumber | ✅ |
| 9 | Số Linh Hồn | SoulsNumber | ✅ |
| 10 | Số Nhân Cách | MatureNumber | ✅ |
| 11 | Số Trưởng Thành | DevelopmentNumber | ✅ |
| 12 | Số Phát Triển | GrowthNumber | ✅ |
| 13 | Số Nội Cảm | KarmicNumber (mode tên) | ✅ |
| 14 | **Số Nợ Nghiệp** | KarmicDebtNumber | ❌ **GAP** |
| 15 | Số Thiếu | MissNumber / leak_num | ✅ |
| 16 | Thể Nhân Dạng | Identifiable | ✅ |
| 17 | Số Điện Thoại | PhoneNumber | ✅ (điều kiện có phone) |
| 18 | **Năm Cá Nhân** | PersonalYearNumber | ❌ **GAP** |
| 19 | Tháng Cá Nhân | PersonalMonthNumber | ✅ |
| 20 | Tài Liệu Tham Khảo (static) | n/a | — |

## GAP chính (P1 — thiếu hẳn mục có trong MỤC LỤC)

### G1. Số Nợ Nghiệp (Karmic Debt 13/4, 14/5, 16/7, 19/1) — THIẾU TOÀN BỘ
- **Calc:** `calculate_numerology_numbers` KHÔNG phát hiện nợ nghiệp. Helper `karmic_debt()` mà memory ghi nhận **đã bị xóa** khi re-squash alembic — grep `app/core/*.py app/services/*.py` rỗng. Dict trả về không có field nợ nghiệp nào.
- **Builder:** `build_report_view` không import/đọc `KarmicDebtNumber`.
- **Data:** bảng `karmic_debt_number` tồn tại + map trong `seed_content.py`, nhưng không có script seed riêng (memory nhắc `seed_karmic_debt.py` — file này KHÔNG còn). Cần xác minh bảng có nội dung.
- **Báo cáo chuẩn:** mục riêng + "GIẢI PHÁP HÓA GIẢI" cho từng mã (đoạn 320-356 docx).
- **Việc cần:** (a) thêm hàm phát hiện karmic debt từ các tổng trung gian (ngày/tháng/năm/chủ đạo/sứ mệnh) trước khi rút gọn; (b) expose list mã 13/14/16/19 trong calc; (c) builder render section + nội dung giải pháp; (d) seed nội dung.

### G2. Số Năm Cá Nhân (Personal Year) — THIẾU
- **Calc:** chỉ tính `_so_nam_ca_nhan` làm biến nội bộ cho Tháng Cá Nhân, **không return** (numerology.py:90, comment "no longer exposed").
- **Builder:** không đọc `PersonalYearNumber` (chỉ có Tháng Cá Nhân).
- **Data:** bảng `personal_year_number` (mã 1-9,10,11) tồn tại; memory ghi pack content KHÔNG có nội dung năm cá nhân → có thể đang dùng row placeholder cũ → cần xác minh.
- **Báo cáo chuẩn:** mục Năm Cá Nhân với diễn giải PYN 1-9 (đoạn 385-457 docx).
- **Việc cần:** expose `so_nam_ca_nhan` trong calc dict + builder thêm `add("SỐ NĂM CÁ NHÂN …", PersonalYearNumber, code)`.

## GAP phụ (P2 — trong mục có sẵn nhưng thiếu thành phần)

### G3. Biểu Đồ Tên + Biểu Đồ Tổng Hợp (Tên & Ngày Sinh)
- Docx có "BIỂU ĐỒ TÊN SAMPLE" (đoạn 270) và "BIỂU ĐỒ TỔNG HỢP TÊN & NGÀY SINH" (273).
- Calc đã có `text_name` (giá trị từng chữ cái) → đủ để dựng biểu đồ tên. Nhưng `build_report_view` chỉ render lưới ngày sinh (`chart_grid`); **không** dựng lưới tên, **không** dựng lưới tổng hợp. Bảng `name_chart` không được đọc bất kỳ đâu (grep rỗng).
- JSON summary (`build_report`) có `power_chart.name` nhưng báo cáo dài thì không.

### G4. Mũi Tên (Arrows of Strength / Empty Arrows) — KHÔNG TÍNH
- Docx nhắc nhiều: Mũi tên Hoạt động (7-8-9), Trí thông minh (3-6-9), mũi tên cá tính, "ốc đảo cô đơn" (số lẻ loi 1/3/7/9).
- Hệ thống **không có** logic tính mũi tên (đủ/thiếu hàng-cột-chéo) và không có bảng nội dung mũi tên. Không nằm thành mục riêng trong MỤC LỤC nhưng là nội dung diễn giải kỳ vọng trong Biểu Đồ Ngày Sinh.

### G5. Diễn giải "KHÔNG CÓ SỐ X" trong biểu đồ ngày sinh
- Docx có các đoạn "SỐ 1 LẺ LOI", "CON SỐ 7 ĐƠN ĐỘC", "KHÔNG CÓ SỐ 7 TRONG NGÀY SINH" (đoạn 109/165/170/193).
- Builder chỉ lặp digit **có mặt** (`for d in sorted(c for c in present if present[c])`) → bỏ qua diễn giải số vắng mặt / lẻ loi (một phần trùng Số Thiếu nhưng ngữ cảnh biểu đồ khác).

### G6. Hiển thị mã master/compound (vd Số Chủ Đạo "10/10", "22/4", "11/2")
- Bảng 6 docx hiển thị dạng kép `10/10`, Biểu đồ chuẩn dùng 11/22/33 (bảng 4).
- Hệ thống rút gọn về 1-9 ở nhiều chỉ số (memory: master preservation cố ý chưa làm cho Ngày/Tháng/Năm/Trưởng Thành). Lệch trình bày so với báo cáo chuẩn.

## Quan sát phụ (không phải gap nội dung, nên dọn)
- Bảng ORM **mồ côi** (không builder nào đọc): `introspective_number`, `deficit_number`, `phone_master_data`. (Số Nội Cảm dùng `karmic_number`; Số Thiếu dùng `miss_number`.) → nợ kỹ thuật, cân nhắc xóa hoặc nối lại.

## Ưu tiên đề xuất
1. **G1 Số Nợ Nghiệp** + **G2 Năm Cá Nhân** — bắt buộc, là mục độc lập trong MỤC LỤC đang thiếu hẳn. Mỗi cái = (calc expose) + (builder add) + (verify/seed nội dung).
2. **G3 Biểu Đồ Tên/Tổng Hợp** — bổ sung trực quan, calc đã sẵn dữ liệu.
3. **G4 Mũi Tên** — tính năng diễn giải mới, cần thiết kế logic + nội dung (effort cao nhất).
4. **G5/G6** — hoàn thiện diễn giải biểu đồ + định dạng master.

## Câu hỏi chưa giải đáp
1. Bảng `karmic_debt_number`, `personal_year_number`, `name_chart` hiện CÓ nội dung thật trong DB prod chưa? (cần query xác minh — quyết định scope là "chỉ nối builder" hay "phải biên soạn + seed nội dung").
2. Mũi Tên (G4) có nằm trong phạm vi bàn giao kỳ vọng của khách không, hay chỉ là nội dung minh họa trong sách? (ảnh hưởng lớn tới effort).
3. Định dạng master/compound (10/10) — khách yêu cầu hiển thị dạng kép hay chấp nhận rút gọn 1-9?
