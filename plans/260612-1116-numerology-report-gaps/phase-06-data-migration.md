# Phase 06 — Data & Migration

**Priority:** P1 (độc lập, làm sớm) · **Status:** pending · **Depends:** none
**Files:** `numerology-api/alembic/versions/<hash>_clean_birthday_chart.py` (mới), `scripts/_content_codes.py` (sửa), `scripts/seed_*.py` hoặc 1 script seed nhỏ cho `not_123`.

## A. Dọn mã rác `'20  '` (Q3)
- Hàng `birthday_chart` code=`'20  '` (trailing spaces) là **placeholder** ("Noi dung placeholder cho BirthdayChart ma 20  ").
- **Migration mới** (nối tiếp head hiện tại `d4a9f1c7b302`):
  ```python
  def upgrade():
      op.execute("DELETE FROM birthday_chart WHERE code = '20  '")
  def downgrade():
      pass  # placeholder rác, không phục hồi
  ```
- Gỡ `"20  ",` khỏi `_BIRTHDAY_CHART` trong `scripts/_content_codes.py` để reseed không tái tạo.
- ⚠️ Lưu ý STRANDED-DB (memory): prod có thể còn stamp ở rev numeric cũ → kiểm tra `alembic current` trước khi `upgrade`; nếu lệch, reconcile + `alembic stamp head --purge` theo memory.

## B. Bổ sung nội dung mũi tên trống `not_123` (Q2)
- DB hiện có 7 mũi tên trống (`not_147,not_159,not_258,not_357,not_369,not_456,not_789`) — **thiếu `not_123`**.
- `123` = trục dọc trái (1-2-3) = **Mũi tên Tổ chức/Thực tế (Planner/Practicality)**; trống = thiếu khả năng sắp xếp, lập kế hoạch, theo trình tự.
- **Thêm 1 hàng** `birthday_chart(code='not_123', title='MŨI TÊN TRỐNG 1-2-3', content=<HTML>)`.
  - Thêm `"not_123",` vào `_BIRTHDAY_CHART` (`_content_codes.py`).
  - Seed: upsert qua script seed hiện có (`seed_content.py`) hoặc INSERT trong cùng migration A (idempotent, `ON CONFLICT (code) DO NOTHING`).
- **Nguồn text:** ưu tiên tài liệu gốc của khách (Cung Khắc Lược / sách Hữu Thiện). Nếu chưa có → dùng **bản nháp** dưới, đánh dấu `<!-- DRAFT: cần khách duyệt -->`:
  > Người thiếu cả 1, 2 và 3 trong biểu đồ ngày sinh mang Mũi tên Trống Tổ chức. Họ thường gặp khó khăn trong việc sắp xếp công việc theo thứ tự, dễ trì hoãn và thiếu kế hoạch rõ ràng… (hoàn thiện theo nguồn khách).

## Todo
- [ ] Tạo migration `clean_birthday_chart` (DELETE '20  ' + optional INSERT not_123).
- [ ] Gỡ `'20  '`, thêm `'not_123'` trong `_content_codes.py`.
- [ ] Seed/insert nội dung `not_123` (draft nếu chưa có nguồn).
- [ ] `docker exec numerology-api-api-1 alembic upgrade head` → không lỗi.
- [ ] Verify: `SELECT count(*) FROM birthday_chart WHERE code IN ('20  ','not_123')` → 0 cho '20  ', 1 cho not_123.

## Success criteria
- Mã rác `'20  '` biến mất khỏi mọi env (dev + prod sau deploy).
- `not_123` có content → P1 phát mũi tên trống đủ 8 line, P2 render được.

## Câu hỏi mở
- Nguồn text chính thức `not_123` từ khách? (nếu không kịp → giữ DRAFT, tạo task theo dõi duyệt nội dung).
