# ruff: noqa: UP017, UP045, I001
"""Tests for FeatureFlagService (Phase 08).

Covers: disabled flag, full rollout, partial rollout deterministic bucketing,
cache invalidation on write.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.chat.feature_flag_service import FeatureFlagService


@pytest.fixture(autouse=True)
def _clear_cache_between_tests():
    FeatureFlagService.invalidate()
    yield
    FeatureFlagService.invalidate()


class TestFeatureFlagService:
    async def test_disabled_flag_returns_false(self, db_session: AsyncSession):
        svc = FeatureFlagService(db_session)
        await svc.set_flag("test_flag", enabled=False, rollout_percent=100)
        await db_session.flush()
        assert await svc.is_enabled("test_flag", user_id=1) is False

    async def test_full_rollout_returns_true_for_any_user(
        self, db_session: AsyncSession
    ):
        svc = FeatureFlagService(db_session)
        await svc.set_flag("test_flag", enabled=True, rollout_percent=100)
        await db_session.flush()
        for uid in (1, 42, 999, None):
            assert await svc.is_enabled("test_flag", user_id=uid) is True

    async def test_zero_rollout_returns_false(self, db_session: AsyncSession):
        svc = FeatureFlagService(db_session)
        await svc.set_flag("test_flag", enabled=True, rollout_percent=0)
        await db_session.flush()
        for uid in (1, 42, 999):
            assert await svc.is_enabled("test_flag", user_id=uid) is False

    async def test_partial_rollout_deterministic(self, db_session: AsyncSession):
        svc = FeatureFlagService(db_session)
        await svc.set_flag("test_flag", enabled=True, rollout_percent=50)
        await db_session.flush()
        # Same user should consistently return the same answer.
        a = await svc.is_enabled("test_flag", user_id=42)
        b = await svc.is_enabled("test_flag", user_id=42)
        assert a == b
        # Across many users, roughly half should be inside the bucket.
        in_count = 0
        total = 500
        for uid in range(1, total + 1):
            if await svc.is_enabled("test_flag", user_id=uid):
                in_count += 1
        ratio = in_count / total
        assert 0.35 <= ratio <= 0.65  # generous bounds for hash distribution

    async def test_unknown_flag_returns_false(self, db_session: AsyncSession):
        svc = FeatureFlagService(db_session)
        assert await svc.is_enabled("missing_flag", user_id=1) is False

    async def test_set_flag_invalidates_cache(self, db_session: AsyncSession):
        svc = FeatureFlagService(db_session)
        await svc.set_flag("test_flag", enabled=False, rollout_percent=0)
        await db_session.flush()
        assert await svc.is_enabled("test_flag", user_id=1) is False
        await svc.set_flag("test_flag", enabled=True, rollout_percent=100)
        await db_session.flush()
        assert await svc.is_enabled("test_flag", user_id=1) is True
