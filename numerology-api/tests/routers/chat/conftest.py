# ruff: noqa: UP017, UP045, I001
"""Per-package fixtures for chat router tests (Phase 08).

Auto-enables the `chatbot_public` feature flag and clears the in-process
FeatureFlagService cache for every test. Without this, every request to
/api/chat/conversations/* gets a 503 from the hardening gate.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.chat.feature_flag_service import FeatureFlagService


@pytest.fixture(autouse=True)
async def _enable_chatbot_public_flag(db_session_factory):
    """Insert chatbot_public=true (100% rollout) before each test."""
    FeatureFlagService.invalidate()
    async with db_session_factory() as db:
        await db.execute(
            text(
                "INSERT INTO chat_feature_flags (flag_key, enabled, rollout_percent) "
                "VALUES ('chatbot_public', 1, 100) "
                "ON CONFLICT (flag_key) DO UPDATE SET enabled=1, rollout_percent=100"
            )
        )
        await db.commit()
    yield
    FeatureFlagService.invalidate()
