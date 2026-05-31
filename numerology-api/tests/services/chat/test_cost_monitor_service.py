# ruff: noqa: UP017, UP045, I001
"""Tests for CostMonitorService and pricing math (Phase 08).

Runs against in-memory SQLite via the shared db_session fixture. The model
ChatDailyMetrics is registered in app/db/models/chat/__init__.py so
Base.metadata.create_all() materialises the table.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.chat.cost_monitor_service import (
    PRICING,
    CostMonitorService,
    calc_msg_cost,
)


class TestCalcMsgCost:
    def test_flash_full_input_full_output(self):
        # 1M flash input = $0.10, 1M flash output = $0.40 → total $0.50
        cost = calc_msg_cost("gemini-2.0-flash", 1_000_000, 1_000_000)
        assert cost == Decimal("0.500000")

    def test_with_cached_tokens_charges_lower_rate(self):
        # 1000 input total, 500 of them cached. Flash cached = $0.025/M, normal = $0.10/M.
        cost = calc_msg_cost("gemini-2.0-flash", 1000, 0, cached_tokens=500)
        # 500*0.10/1M + 500*0.025/1M = 0.00005 + 0.0000125 = 0.0000625
        assert cost == Decimal("0.000063") or cost == Decimal("0.0000625".rstrip("0") or "0")

    def test_unknown_model_returns_zero(self, caplog):
        cost = calc_msg_cost("imaginary-model", 1000, 500)
        assert cost == Decimal("0")

    def test_pricing_table_has_required_models(self):
        for m in ("gemini-2.0-flash", "gemini-2.5-pro", "text-embedding-004"):
            assert m in PRICING
            assert "input" in PRICING[m]
            assert "output" in PRICING[m]


class TestCostMonitorService:
    async def test_record_message_cost_inserts_today_row(
        self, db_session: AsyncSession
    ):
        svc = CostMonitorService(db_session)
        cost = await svc.record_message_cost(
            "gemini-2.0-flash", 1000, 500, tier="free"
        )
        await db_session.flush()
        assert cost > 0
        today = datetime.now(timezone.utc).date()
        row = (
            await db_session.execute(
                text(
                    "SELECT msg_count_free, msg_count_paid, input_tokens_total, "
                    "output_tokens_total, cost_usd "
                    "FROM chat_daily_metrics WHERE date = :d"
                ),
                {"d": today},
            )
        ).first()
        assert row is not None
        assert int(row[0]) == 1
        assert int(row[1]) == 0
        assert int(row[2]) == 1000
        assert int(row[3]) == 500
        assert Decimal(str(row[4])) > 0

    async def test_record_message_cost_increments_existing(
        self, db_session: AsyncSession
    ):
        svc = CostMonitorService(db_session)
        await svc.record_message_cost("gemini-2.0-flash", 100, 50, tier="free")
        await svc.record_message_cost("gemini-2.0-flash", 200, 100, tier="paid")
        await db_session.flush()
        today = datetime.now(timezone.utc).date()
        row = (
            await db_session.execute(
                text(
                    "SELECT msg_count_free, msg_count_paid, input_tokens_total "
                    "FROM chat_daily_metrics WHERE date = :d"
                ),
                {"d": today},
            )
        ).first()
        assert int(row[0]) == 1
        assert int(row[1]) == 1
        assert int(row[2]) == 300

    async def test_increment_rate_limit_hit(self, db_session: AsyncSession):
        svc = CostMonitorService(db_session)
        await svc.increment_rate_limit_hit()
        await svc.increment_rate_limit_hit()
        await db_session.flush()
        today = datetime.now(timezone.utc).date()
        row = (
            await db_session.execute(
                text(
                    "SELECT rate_limit_hits FROM chat_daily_metrics WHERE date = :d"
                ),
                {"d": today},
            )
        ).first()
        assert int(row[0]) == 2

    async def test_get_today_cost_zero_when_empty(self, db_session: AsyncSession):
        svc = CostMonitorService(db_session)
        assert await svc.get_today_cost() == Decimal("0")

    async def test_alert_returns_false_when_below_threshold(
        self, db_session: AsyncSession
    ):
        svc = CostMonitorService(db_session)
        await svc.record_message_cost("gemini-2.0-flash", 10, 5, tier="free")
        await db_session.flush()
        fired = await svc.alert_if_exceeded(threshold_usd=Decimal("100"))
        assert fired is False

    async def test_cache_hit_counter(self, db_session: AsyncSession):
        svc = CostMonitorService(db_session)
        await svc.record_message_cost(
            "gemini-2.0-flash", 0, 0, tier="free", from_cache=True
        )
        await db_session.flush()
        today = datetime.now(timezone.utc).date()
        row = (
            await db_session.execute(
                text("SELECT cache_hits FROM chat_daily_metrics WHERE date = :d"),
                {"d": today},
            )
        ).first()
        assert int(row[0]) == 1
