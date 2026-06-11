"""drop balance_number & execution_number

Số Cân Bằng (balance) and Số Thực Thi (execution) were removed from the
numerology algorithm — they have no counterpart in the authoritative Excel
template. Their content tables are now orphaned, so drop them.

Revision ID: b2e7c9a4d810
Revises: a1d6e2c84f31
Create Date: 2026-06-10 20:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2e7c9a4d810'
down_revision: Union[str, None] = 'a1d6e2c84f31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f('ix_balance_number_code'), table_name='balance_number')
    op.drop_table('balance_number')
    op.drop_index(op.f('ix_execution_number_code'), table_name='execution_number')
    op.drop_table('execution_number')


def _create_content_table(name: str) -> None:
    """Re-create a standard numerology content table (NumerologyContentMixin shape)."""
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


def downgrade() -> None:
    # Re-create empty tables — historical content rows are not recoverable.
    _create_content_table('execution_number')
    _create_content_table('balance_number')
