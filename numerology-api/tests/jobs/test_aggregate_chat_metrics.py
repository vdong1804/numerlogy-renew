# ruff: noqa: UP017, UP045, I001
"""Tests for aggregate_chat_metrics job (Phase 08).

Strategy: seed chat_messages + chat_conversations directly via SQL, run
_recompute_for_date, and assert chat_daily_metrics row reflects the seeded
counts/costs.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.aggregate_chat_metrics import _recompute_for_date


async def _seed_user(db: AsyncSession, user_id: int) -> None:
    await db.execute(
        text(
            "INSERT INTO users (id, email, first_name, last_name, is_active, is_superuser, "
            "chat_abuse_score, chat_captcha_required, chat_captcha_solve_count) "
            "VALUES (:id, :em, '', '', 1, 0, 0, 0, 0)"
        ),
        {"id": user_id, "em": f"u{user_id}@x.com"},
    )


async def _seed_conv(db: AsyncSession, conv_id: int, user_id: int) -> None:
    await db.execute(
        text(
            "INSERT INTO chat_conversations (id, user_id, title, pdf_context_id, "
            "created_at, updated_at) "
            "VALUES (:c, :u, 't', NULL, :ts, :ts)"
        ),
        {"c": conv_id, "u": user_id, "ts": datetime.now(timezone.utc)},
    )


async def _seed_message(
    db: AsyncSession,
    msg_id: int,
    conv_id: int,
    role: str,
    *,
    model_used: str | None = None,
    tier: str | None = "free",
    input_tokens: int = 0,
    output_tokens: int = 0,
    created_at: datetime | None = None,
) -> None:
    ts = created_at or datetime.now(timezone.utc)
    await db.execute(
        text(
            "INSERT INTO chat_messages (id, conversation_id, role, content, model_used, "
            "tier, input_tokens, output_tokens, citations, created_at) "
            "VALUES (:id, :c, :r, 'hello', :m, :t, :i, :o, '[]', :ts)"
        ),
        {
            "id": msg_id, "c": conv_id, "r": role, "m": model_used,
            "t": tier, "i": input_tokens, "o": output_tokens, "ts": ts,
        },
    )


class TestAggregateChatMetrics:
    async def test_recompute_zero_when_no_messages(self, db_session: AsyncSession):
        today = datetime.now(timezone.utc).date()
        stats = await _recompute_for_date(db_session, today)
        await db_session.flush()
        assert stats["msg_free"] == 0
        assert stats["msg_paid"] == 0
        assert stats["cache_hits"] == 0
        assert Decimal(stats["cost_usd"]) == Decimal("0")

    async def test_recompute_counts_free_vs_paid(self, db_session: AsyncSession):
        await _seed_user(db_session, 10)
        await _seed_conv(db_session, 100, 10)
        await _seed_message(
            db_session, 1000, 100, "assistant",
            model_used="gemini-2.0-flash", tier="free",
            input_tokens=100, output_tokens=50,
        )
        await _seed_message(
            db_session, 1001, 100, "assistant",
            model_used="gemini-2.5-pro", tier="paid",
            input_tokens=200, output_tokens=100,
        )
        await db_session.flush()
        today = datetime.now(timezone.utc).date()
        stats = await _recompute_for_date(db_session, today)
        await db_session.flush()
        assert stats["msg_free"] == 1
        assert stats["msg_paid"] == 1
        assert Decimal(stats["cost_usd"]) > 0

    async def test_recompute_cache_hits(self, db_session: AsyncSession):
        await _seed_user(db_session, 11)
        await _seed_conv(db_session, 101, 11)
        await _seed_message(
            db_session, 2000, 101, "assistant",
            model_used="cache", tier="free",
        )
        await db_session.flush()
        today = datetime.now(timezone.utc).date()
        stats = await _recompute_for_date(db_session, today)
        assert stats["cache_hits"] == 1
        # Cache hits should NOT contribute to cost.
        assert Decimal(stats["cost_usd"]) == Decimal("0")

    async def test_recompute_idempotent(self, db_session: AsyncSession):
        """Re-running the same recompute overwrites rather than accumulates."""
        await _seed_user(db_session, 12)
        await _seed_conv(db_session, 102, 12)
        await _seed_message(
            db_session, 3000, 102, "assistant",
            model_used="gemini-2.0-flash", tier="free",
            input_tokens=100, output_tokens=50,
        )
        await db_session.flush()
        today = datetime.now(timezone.utc).date()
        a = await _recompute_for_date(db_session, today)
        await db_session.flush()
        b = await _recompute_for_date(db_session, today)
        await db_session.flush()
        assert a == b
        # And the row count is still 1, not 2.
        row_count = (
            await db_session.execute(
                text("SELECT COUNT(*) FROM chat_daily_metrics WHERE date = :d"),
                {"d": today},
            )
        ).scalar_one()
        assert int(row_count) == 1

    async def test_unique_users_counted(self, db_session: AsyncSession):
        await _seed_user(db_session, 21)
        await _seed_user(db_session, 22)
        await _seed_conv(db_session, 201, 21)
        await _seed_conv(db_session, 202, 22)
        await _seed_message(
            db_session, 4001, 201, "user", model_used=None, tier="free",
        )
        await _seed_message(
            db_session, 4002, 202, "user", model_used=None, tier="free",
        )
        await db_session.flush()
        today = datetime.now(timezone.utc).date()
        stats = await _recompute_for_date(db_session, today)
        assert stats["unique_users"] == 2
