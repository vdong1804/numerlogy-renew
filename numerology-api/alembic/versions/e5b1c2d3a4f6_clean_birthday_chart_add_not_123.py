"""clean birthday_chart placeholders + add empty-arrow not_123 content

Two data fixes for the Pythagoras birth-chart content table:
  1. Delete ALL leftover placeholder rows (content "Noi dung placeholder cho
     BirthdayChart ma …"). This removes the junk code '20  ' AND fixes a data
     bug: the 8 arrow codes (123/147/159/258/357/369/456/789) each had BOTH a
     placeholder row and the real-content row under the same code, so
     fetch_by_code(...).scalar_one_or_none() raised MultipleResultsFound. After
     cleanup each arrow resolves to exactly one real row. Placeholder-only codes
     (count variants {d}_1..{d}_5, isolated {d}_single) become absent → the
     report skips them cleanly instead of rendering placeholder text.
  2. Add the missing empty-arrow row code='not_123'. The DB shipped 7 of the 8
     empty arrows (not_147/159/258/357/369/456/789) but lacked not_123, so the
     report could never render the empty Arrow of Practicality (left column
     1-2-3). Content below is a DRAFT — replace with client's source text.

Revision ID: e5b1c2d3a4f6
Revises: d4a9f1c7b302
Create Date: 2026-06-12 11:40:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e5b1c2d3a4f6'
down_revision: Union[str, None] = 'd4a9f1c7b302'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# DRAFT content — Mũi Tên Trống 1-2-3 (empty Planning Arrow). The source corpus
# ("Nôi dung/2 BIỂU ĐỒ NGÀY SINH") ships the 7 other empty arrows but NOT this
# one, so it is authored here in the same voice (themed "Kế Hoạch", matching the
# strength file "MŨI TÊN 123 MT KẾ HOẠCH"). TODO: replace with client source text.
_NOT_123_TITLE = "MŨI TÊN TRỐNG 1-2-3. MŨI TÊN THIẾU KẾ HOẠCH"
_NOT_123_CONTENT = (
    "<!-- DRAFT: cần khách duyệt -->"
    "<p>Ngược với Mũi tên Kế hoạch 1-2-3 (hội tụ cái tôi số 1, trực giác số 2 và "
    "óc phân tích số 3 thành khả năng lập kế hoạch mạch lạc), người thiếu vắng cả "
    "ba số 1, 2 và 3 trong biểu đồ ngày sinh mang <strong>Mũi tên Trống Kế hoạch</strong> "
    "(trục dọc trái 1-2-3).</p>"
    "<p>Đây là dấu hiệu cho thấy việc vạch ra một lộ trình tổng thể, sắp xếp công việc "
    "theo trình tự và kiên trì đi tới đích chưa phải là thế mạnh tự nhiên. Những người "
    "này dễ khởi sự nhiều việc cùng lúc, hành động theo cảm hứng hơn là theo một kế "
    "hoạch rõ ràng, và đôi khi bỏ dở giữa chừng khi thiếu một khung trình tự dẫn dắt.</p>"
    "<p>Bài học là tập tư duy có phương pháp: viết mục tiêu ra giấy, chia nhỏ thành "
    "từng bước có thứ tự và bám theo một danh sách công việc. Người có Số Chủ Đạo 4, 7 "
    "hoặc Mũi tên Thực tế 1-4-7 sẽ bù đắp được điểm này dễ hơn. Khi rèn được thói quen "
    "lập kế hoạch, họ hoàn toàn có thể biến sự ngẫu hứng thành sức sáng tạo có tổ chức.</p>"
)


def upgrade() -> None:
    bind = op.get_bind()
    # 1. Remove ALL placeholder rows (covers junk '20  ' + duplicate arrow rows).
    bind.execute(sa.text(
        "DELETE FROM birthday_chart "
        "WHERE content LIKE '%placeholder cho BirthdayChart%'"
    ))
    # 2. Insert not_123 (idempotent — skip if already seeded).
    bind.execute(
        sa.text(
            "INSERT INTO birthday_chart (code, title, content) "
            "VALUES (:code, :title, :content) "
            "ON CONFLICT (code) DO NOTHING"
        ),
        {"code": "not_123", "title": _NOT_123_TITLE, "content": _NOT_123_CONTENT},
    )


def downgrade() -> None:
    # Junk placeholder is not restored (intentional). Remove the seeded row.
    op.execute("DELETE FROM birthday_chart WHERE code = 'not_123'")
