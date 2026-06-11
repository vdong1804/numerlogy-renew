"""convert all naive timestamp columns to timestamptz

A schema refactor left many timestamp columns as `timestamp without time zone`
while the codebase uniformly uses timezone-aware datetimes
(`datetime.now(timezone.utc)`). Filtering a naive column with an aware param
raises asyncpg DataError ("can't subtract offset-naive and offset-aware
datetimes"), crashing scheduled jobs (detect_chat_abuse, etc.).

This converts every currently-naive timestamp column to `timestamptz`.
Safe because every such column uses `server_default=func.now()` — the DB
generates the value, so no Python naive datetime is ever inserted. Existing
values are interpreted as UTC.

Revision ID: d4a9f1c7b302
Revises: c3f8a1b6e920
Create Date: 2026-06-11 14:54:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4a9f1c7b302'
down_revision: Union[str, None] = 'c3f8a1b6e920'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (table, column) pairs that are currently `timestamp without time zone`.
_NAIVE_TIMESTAMP_COLUMNS = [
    ('chat_conversations', 'created_at'),
    ('chat_conversations', 'updated_at'),
    ('chat_messages', 'created_at'),
    ('email_outbox', 'created_at'),
    ('email_outbox', 'updated_at'),
    ('kb_documents', 'created_at'),
    ('kb_documents', 'updated_at'),
    ('news', 'created_at'),
    ('news', 'updated_at'),
    ('orders', 'created_at'),
    ('orders', 'updated_at'),
    ('packages', 'created_at'),
    ('packages', 'updated_at'),
    ('products', 'created_at'),
    ('products', 'updated_at'),
    ('user_downloads', 'created_at'),
    ('user_packages', 'created_at'),
    ('user_packages', 'updated_at'),
    ('user_payments', 'created_at'),
    ('user_payments', 'updated_at'),
    ('user_profiles', 'created_at'),
    ('user_profiles', 'updated_at'),
    ('users', 'created_at'),
    ('users', 'updated_at'),
]


def upgrade() -> None:
    for table, column in _NAIVE_TIMESTAMP_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=True),
            postgresql_using=f'"{column}" AT TIME ZONE \'UTC\'',
        )


def downgrade() -> None:
    for table, column in _NAIVE_TIMESTAMP_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=False),
            postgresql_using=f'"{column}" AT TIME ZONE \'UTC\'',
        )
