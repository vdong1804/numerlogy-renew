# ruff: noqa: UP017, UP045, I001
"""Tests for AbTestService deterministic variant assignment (Phase 08)."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.chat.ab_test_service import AbTestService


class TestAbTestService:
    async def test_assigns_variant_on_first_lookup(self, db_session: AsyncSession):
        svc = AbTestService(db_session)
        variant = await svc.get_or_assign_variant(user_id=7777)
        await db_session.flush()
        assert variant in ("control", "variant_a", "variant_b")
        row = (
            await db_session.execute(
                text(
                    "SELECT variant FROM chat_ab_test_assignments WHERE user_id = :u"
                ),
                {"u": 7777},
            )
        ).first()
        assert row is not None
        assert row[0] == variant

    async def test_same_user_returns_same_variant(self, db_session: AsyncSession):
        svc = AbTestService(db_session)
        a = await svc.get_or_assign_variant(user_id=8888)
        await db_session.flush()
        b = await svc.get_or_assign_variant(user_id=8888)
        assert a == b

    async def test_distribution_roughly_matches_split(self, db_session: AsyncSession):
        svc = AbTestService(db_session)
        counts = {"control": 0, "variant_a": 0, "variant_b": 0}
        total = 500
        for uid in range(1, total + 1):
            v = await svc.get_or_assign_variant(user_id=uid)
            counts[v] += 1
        # Default split: ~10% variant_a, ~10% variant_b, ~80% control.
        assert counts["control"] / total > 0.65
        assert 0.03 <= counts["variant_a"] / total <= 0.18
        assert 0.03 <= counts["variant_b"] / total <= 0.18
