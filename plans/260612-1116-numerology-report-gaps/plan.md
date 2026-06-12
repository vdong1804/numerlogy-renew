# Plan: Bù GAP báo cáo Thần Số Học (G1–G6)

**Mục tiêu:** Đưa báo cáo hệ thống khớp đầy đủ MỤC LỤC báo cáo chuẩn `SAMPLE 00.00.2000.docx`.
**Nguồn GAP:** `plans/reports/analysis-260612-1107-sample-docx-report-gap.md`
**Phát hiện then chốt:** Nội dung 6 GAP **đã có sẵn trong DB** (karmic_debt_number=4, personal_year_number=11, name_chart=9; mũi tên `147/258/369/123/456/789/159/357` + `not_*` và số lẻ loi `{d}_single` đã có trong birthday_chart=82). ⇒ Công việc = **logic calc + nối builder + template/frontend + tests**, KHÔNG biên soạn nội dung.

## Quyết định đã chốt
- **Nợ Nghiệp:** phát hiện từ **5 chỉ số cốt lõi** (Chủ Đạo, Sứ Mệnh, Linh Hồn, Nhân Cách, Ngày Sinh) — tổng trước rút gọn ∈ {13,14,16,19}.
- **Hiển thị master:** chỉ **Số Chủ Đạo** + **Số Nợ Nghiệp** dạng kép (`22/4`, `13/4`); các số khác dạng đơn (1-9). ⇒ Năm Cá Nhân rút về 1-9.
- **Phạm vi:** cập nhật cả báo cáo dài (`build_report_view` + invoice.html) VÀ JSON tóm tắt (`build_report` + landing).

## GAP → Phase
| GAP | Nội dung | Phase chính |
|---|---|---|
| G1 | Số Nợ Nghiệp (13/14/16/19) | P1 calc + P2/P3 builder |
| G2 | Năm Cá Nhân | P1 expose + P2/P3 builder |
| G3 | Biểu Đồ Tên + Tổng Hợp | P1 name_counts + P2/P3/P4 |
| G4 | Mũi Tên (mạnh/trống) | P1 logic + P2/P3 fetch |
| G5 | Số lẻ loi (`{d}_single`) | P1 logic + P2 fetch |
| G6 | Hiển thị kép Chủ Đạo/Nợ Nghiệp | P1 compound + P2/P3 hiển thị |

## Phases
- [x] **P1 — Calc layer** ✅ → `phase-01-calc-layer.md` — `numerology_chart.py` (arrows/isolated/karmic/compound/derive_chart_fields) + calc expose 6 nhóm trường. 49/49 unit test pass.
- [x] **P2 — Full report builder** ✅ → `numerology_full_report.py`: Nợ Nghiệp, Năm Cá Nhân, biểu đồ tên+tổng hợp, mũi tên (mạnh/trống incl not_123), compound chủ đạo, summary. Verified qua DB thật. (Phụ: migration mở rộng xóa toàn bộ 57 placeholder birthday_chart → fix dup arrow MultipleResultsFound.)
- [x] **P3 — JSON summary builder** ✅ → `numerology_report_builder.py` + `numerology_db.py`: karmic_debt, personal.nam_ca_nhan, name_chart, arrows, compound, power_chart.combined. Verified.
- [x] **P4 — Template + Frontend** ✅ → invoice.html (biểu đồ tên + tổng hợp, string-repeat grid; mục text mới auto-render). Landing: `numerology-report.ts` types mở rộng, `KarmicDebtSection` mới + wire `ket-qua`, PersonalCycleSection thêm năm cá nhân. tsc sạch (file đã sửa).
- [x] **P5 — Tests** ✅ → `test_numerology_chart.py` (unit thuần) + `test_numerology_report_builder.py` (structural, SQLite). 71/71 pass; 12/12 endpoint integration pass (4 fail cũ nay xanh). Không hồi quy.
- [x] **P6 — Data & Migration** ✅ → `phase-06-data-migration.md` — migration `e5b1c2d3a4f6` (xóa `'20  '` + seed `not_123` DRAFT) đã upgrade dev DB. `_content_codes.py` cập nhật. DRAFT not_123 chờ khách duyệt.

## Dependencies
P6 (data) độc lập. P1 → (P2 ∥ P3) → P4 → P5. P2/P3 song song. P2 fetch `not_123` cần P6 xong (nếu không có content thì guard bỏ qua — không chặn).

## Files chạm chính
- `numerology-api/app/core/numerology.py`, `app/core/numerology_chart.py` (mới)
- `app/services/numerology_full_report.py`, `app/services/numerology_db.py`, `app/services/numerology_report_builder.py`
- `app/templates/invoice.html`
- `Numerology-Landing-Page/src/models/numerology-report.ts`, `src/pages/ket-qua/index.tsx`
- `numerology-api/tests/…` (unit + integration)

## Quyết định bổ sung (đã chốt)
1. Nhiều Nợ Nghiệp → **sort tăng dần** mã.
2. Mũi tên trống `123` → **bổ sung nội dung** (`not_123`) — xem P6. Bỏ guard NOT_AVAILABLE ở P1.
3. Mã rác `'20  '` → **dọn bằng migration** + gỡ khỏi `_content_codes.py` (P6).

## Câu hỏi mở
1. Text chuẩn cho `not_123` (Mũi tên trống Tổ chức/Thực tế, trục dọc 1-2-3) lấy từ tài liệu gốc nào của khách? (P6 cần nguồn; tạm có bản nháp).
