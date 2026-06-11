"""add karmic_debt_number & growth_number

New content tables for Số Nợ Nghiệp (karmic debt: 13/14/16/19) and
Số Phát Triển (growth / năng lực tiếp cận), migrated from the Nội dung corpus.

Revision ID: c3f8a1b6e920
Revises: b2e7c9a4d810
Create Date: 2026-06-10 21:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3f8a1b6e920'
down_revision: Union[str, None] = 'b2e7c9a4d810'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_content_table(name: str) -> None:
    """Create a standard numerology content table (NumerologyContentMixin shape)."""
    op.create_table(
        name,
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=255), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('number_page', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f(f'ix_{name}_code'), name, ['code'], unique=True)


def upgrade() -> None:
    _create_content_table('karmic_debt_number')
    _create_content_table('growth_number')


def downgrade() -> None:
    op.drop_index(op.f('ix_growth_number_code'), table_name='growth_number')
    op.drop_table('growth_number')
    op.drop_index(op.f('ix_karmic_debt_number_code'), table_name='karmic_debt_number')
    op.drop_table('karmic_debt_number')
