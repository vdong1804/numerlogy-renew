"""Unit tests for PromptSettingsService — cache + audit log + history."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.db.models.chat.system_settings import (
    ChatSystemSetting,
    ChatSystemSettingHistory,
)
from app.services.chat import prompt_settings_service as pss
from app.services.chat.prompt_settings_service import (
    KEY_SYSTEM_PROMPT,
    PromptSettingsService,
    invalidate_cache,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    """Drop module-level cache before every test for isolation."""
    invalidate_cache()
    yield
    invalidate_cache()


@pytest.mark.asyncio
async def test_get_override_returns_none_when_no_row(db_session):
    svc = PromptSettingsService(db_session)
    assert await svc.get_override() is None


@pytest.mark.asyncio
async def test_update_creates_row_and_history(db_session):
    svc = PromptSettingsService(db_session)
    row = await svc.update(KEY_SYSTEM_PROMPT, "first version", updated_by=1)
    assert row.version == 1
    assert row.value == "first version"

    hist = (
        await db_session.execute(select(ChatSystemSettingHistory))
    ).scalars().all()
    assert len(hist) == 1
    assert hist[0].value == "first version"


@pytest.mark.asyncio
async def test_update_bumps_version_and_snapshots_previous(db_session):
    svc = PromptSettingsService(db_session)
    await svc.update(KEY_SYSTEM_PROMPT, "v1", updated_by=1)
    await svc.update(KEY_SYSTEM_PROMPT, "v2", updated_by=2)

    rows = (await db_session.execute(select(ChatSystemSetting))).scalars().all()
    assert len(rows) == 1
    assert rows[0].version == 2
    assert rows[0].value == "v2"

    hist = (
        await db_session.execute(
            select(ChatSystemSettingHistory).order_by(ChatSystemSettingHistory.id)
        )
    ).scalars().all()
    # Two updates → two history rows
    assert len(hist) == 2
    assert hist[0].value == "v1"
    assert hist[0].version == 1
    assert hist[1].value == "v1"
    assert hist[1].version == 1


@pytest.mark.asyncio
async def test_delete_removes_row_and_appends_final_history(db_session):
    svc = PromptSettingsService(db_session)
    await svc.update(KEY_SYSTEM_PROMPT, "v1", updated_by=1)

    assert await svc.delete() is True
    assert await svc.get_current() is None

    hist = (await db_session.execute(select(ChatSystemSettingHistory))).scalars().all()
    # 1 history from update + 1 from delete
    assert len(hist) == 2


@pytest.mark.asyncio
async def test_delete_returns_false_when_no_row(db_session):
    svc = PromptSettingsService(db_session)
    assert await svc.delete() is False


@pytest.mark.asyncio
async def test_get_override_uses_cache(db_session, monkeypatch):
    svc = PromptSettingsService(db_session)
    await svc.update(KEY_SYSTEM_PROMPT, "cached value", updated_by=1)

    # First read populates cache
    assert await svc.get_override() == "cached value"

    # Mutate DB outside the service to confirm cache served us
    row = await svc.get_current()
    assert row is not None
    row.value = "stealth change"
    await db_session.flush()

    # Cache TTL is 60s → still serves the previous value
    assert await svc.get_override() == "cached value"

    # After explicit invalidate we see the new DB value
    invalidate_cache(KEY_SYSTEM_PROMPT)
    assert await svc.get_override() == "stealth change"


@pytest.mark.asyncio
async def test_update_invalidates_cache(db_session):
    svc = PromptSettingsService(db_session)
    await svc.update(KEY_SYSTEM_PROMPT, "v1", updated_by=1)
    assert await svc.get_override() == "v1"

    await svc.update(KEY_SYSTEM_PROMPT, "v2", updated_by=1)
    # Cache should have been dropped by update()
    assert await svc.get_override() == "v2"


@pytest.mark.asyncio
async def test_list_history_ordered_desc(db_session):
    svc = PromptSettingsService(db_session)
    await svc.update(KEY_SYSTEM_PROMPT, "v1", updated_by=1)
    await svc.update(KEY_SYSTEM_PROMPT, "v2", updated_by=1)
    await svc.update(KEY_SYSTEM_PROMPT, "v3", updated_by=1)

    rows = await svc.list_history(KEY_SYSTEM_PROMPT, limit=10)
    # initial row + 2 snapshots from the v2 / v3 updates
    assert len(rows) == 3
    assert rows[0].changed_at >= rows[1].changed_at >= rows[2].changed_at
