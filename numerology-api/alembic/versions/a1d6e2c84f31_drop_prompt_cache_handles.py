"""drop prompt_cache_handles

DeepSeek auto-caches identical prompts server-side, so the Gemini
explicit-cache handle table is no longer needed.

Revision ID: a1d6e2c84f31
Revises: 497b2cb25f8d
Create Date: 2026-06-01 06:32:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1d6e2c84f31'
down_revision: Union[str, None] = '497b2cb25f8d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('prompt_cache_handles')


def downgrade() -> None:
    # Re-create empty table — historical rows are not recoverable.
    op.create_table(
        'prompt_cache_handles',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('cache_key', sa.String(length=200), nullable=False),
        sa.Column('gemini_cache_id', sa.String(length=255), nullable=False),
        sa.Column('model', sa.String(length=50), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key'),
    )
