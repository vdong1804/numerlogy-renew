# ruff: noqa: UP045, UP017
"""Unit tests for PromptCacheService.

Uses in-memory SQLite via the shared db_session fixture.
Gemini client is mocked throughout — no network calls.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat.prompt_cache_handle import PromptCacheHandle
from app.services.chat.prompt_cache_service import (
    PromptCacheResult,
    PromptCacheService,
    _HitCounter,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fake_gemini_client(
    cache_name: str = "caches/abc123",
    token_count: int = 512,
) -> MagicMock:
    """Mock genai.Client whose caches.create() returns a stub CachedContent."""
    usage = SimpleNamespace(total_token_count=token_count)
    cached_content = SimpleNamespace(name=cache_name, usage_metadata=usage)
    client = MagicMock()
    client.caches.create.return_value = cached_content
    return client


def _svc(db: AsyncSession, client: MagicMock | None = None) -> PromptCacheService:
    c = client if client is not None else _fake_gemini_client()
    return PromptCacheService(db=db, client_provider=lambda: c)


def _seed_handle(
    db: AsyncSession,
    cache_key: str,
    gemini_cache_id: str = "caches/seed",
    expires_delta: timedelta = timedelta(hours=1),
) -> PromptCacheHandle:
    row = PromptCacheHandle(
        cache_key=cache_key,
        gemini_cache_id=gemini_cache_id,
        model="gemini-2.0-flash",
        token_count=200,
        expires_at=_now() + expires_delta,
    )
    db.add(row)
    return row


# ---------------------------------------------------------------------------
# 1. compute_key — determinism
# ---------------------------------------------------------------------------


def test_compute_key_deterministic_same_inputs_same_hash():
    k1 = PromptCacheService.compute_key("system", [1, 2, 3], "flash")
    k2 = PromptCacheService.compute_key("system", [1, 2, 3], "flash")
    assert k1 == k2
    assert len(k1) == 64


def test_compute_key_different_tier_different_hash():
    k_flash = PromptCacheService.compute_key("system", [1, 2], "flash")
    k_pro = PromptCacheService.compute_key("system", [1, 2], "pro")
    assert k_flash != k_pro


def test_compute_key_chunk_id_order_invariant():
    """Implementation sorts ids — ordering must not affect the key."""
    k1 = PromptCacheService.compute_key("system", [3, 1, 2], "flash")
    k2 = PromptCacheService.compute_key("system", [1, 2, 3], "flash")
    assert k1 == k2


# ---------------------------------------------------------------------------
# 2. get_live_handle — DB lookup
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_live_handle_returns_none_when_no_row(db_session: AsyncSession):
    svc = _svc(db_session)
    result = await svc.get_live_handle("totally-absent-key")
    assert result is None


@pytest.mark.asyncio
async def test_get_live_handle_returns_none_when_expired(db_session: AsyncSession):
    _seed_handle(db_session, "expired-key", expires_delta=timedelta(hours=-2))
    await db_session.flush()

    svc = _svc(db_session)
    result = await svc.get_live_handle("expired-key")
    assert result is None


@pytest.mark.asyncio
async def test_get_live_handle_returns_result_when_live(db_session: AsyncSession):
    row = _seed_handle(db_session, "live-key", gemini_cache_id="caches/live123")
    await db_session.flush()
    await db_session.refresh(row)

    svc = _svc(db_session)
    result = await svc.get_live_handle("live-key")

    assert result is not None
    assert isinstance(result, PromptCacheResult)
    assert result.gemini_cache_id == "caches/live123"
    assert result.handle_id == row.id


@pytest.mark.asyncio
async def test_get_live_handle_refreshes_expires_at_on_hit(db_session: AsyncSession):
    """TTL should be pushed forward (now + ttl) on every hit."""
    original_expires = _now() + timedelta(minutes=10)
    row = PromptCacheHandle(
        cache_key="refresh-key",
        gemini_cache_id="caches/refresh",
        model="gemini-2.0-flash",
        token_count=300,
        expires_at=original_expires,
    )
    db_session.add(row)
    await db_session.flush()

    svc = _svc(db_session)
    await svc.get_live_handle("refresh-key")
    await db_session.refresh(row)

    # SQLite returns naive datetimes from DateTime(timezone=True) columns;
    # strip tzinfo from original_expires before comparing.
    refreshed = row.expires_at
    if refreshed.tzinfo is None:
        baseline = original_expires.replace(tzinfo=None)
    else:
        baseline = original_expires
    assert refreshed > baseline


# ---------------------------------------------------------------------------
# 3. maybe_create — hit counter + Gemini API
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_maybe_create_first_request_under_threshold_returns_none(
    db_session: AsyncSession,
):
    """Below threshold (default=5) → return None; Gemini not called."""
    cache_key = "under-threshold-key"
    _HitCounter.reset(cache_key)

    client = _fake_gemini_client()
    svc = _svc(db_session, client)

    result = await svc.maybe_create(
        cache_key=cache_key,
        system="system",
        kb_chunks=[{"content": "text", "title": "doc"}],
        tier="flash",
        model="gemini-2.0-flash",
    )

    assert result is None
    client.caches.create.assert_not_called()
    _HitCounter.reset(cache_key)


@pytest.mark.asyncio
async def test_maybe_create_at_threshold_calls_gemini_and_inserts_row(
    db_session: AsyncSession,
):
    """Exactly at threshold → Gemini caches.create called; handle row inserted."""
    from app.config import settings

    cache_key = "at-threshold-key"
    _HitCounter.reset(cache_key)

    client = _fake_gemini_client(cache_name="caches/newcache", token_count=768)
    svc = _svc(db_session, client)

    # Warm up to threshold - 1 (no creation yet)
    for _ in range(settings.prompt_cache_hit_threshold - 1):
        r = await svc.maybe_create(
            cache_key=cache_key,
            system="sys",
            kb_chunks=[{"content": "c", "title": "t"}],
            tier="flash",
            model="gemini-2.0-flash",
        )
        assert r is None

    # Hit the threshold — creation expected
    result = await svc.maybe_create(
        cache_key=cache_key,
        system="sys",
        kb_chunks=[{"content": "c", "title": "t"}],
        tier="flash",
        model="gemini-2.0-flash",
    )

    assert result is not None
    assert result.gemini_cache_id == "caches/newcache"
    assert result.handle_id is not None
    client.caches.create.assert_called_once()
    _HitCounter.reset(cache_key)


@pytest.mark.asyncio
async def test_maybe_create_handles_gemini_api_error_gracefully(
    db_session: AsyncSession,
):
    """Gemini API failure → None returned; no exception propagates to caller."""
    from app.config import settings

    cache_key = "error-key"
    _HitCounter.reset(cache_key)

    client = MagicMock()
    client.caches.create.side_effect = RuntimeError("Gemini unavailable")
    svc = _svc(db_session, client)

    result = None
    for _ in range(settings.prompt_cache_hit_threshold):
        result = await svc.maybe_create(
            cache_key=cache_key,
            system="sys",
            kb_chunks=[{"content": "c", "title": "t"}],
            tier="flash",
            model="gemini-2.0-flash",
        )

    # Threshold hit triggered Gemini which failed — must return None, not raise
    assert result is None
    _HitCounter.reset(cache_key)


# ---------------------------------------------------------------------------
# 4. invalidate_for_chunks — async broad-strokes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalidate_for_chunks_deletes_all_handles(db_session: AsyncSession):
    """Broad-strokes: ALL handles deleted regardless of which chunk ids are passed."""
    for i in range(3):
        row = PromptCacheHandle(
            cache_key=f"inv-key-{i}",
            gemini_cache_id=f"caches/inv{i}",
            model="gemini-2.0-flash",
            token_count=100,
            expires_at=_now() + timedelta(hours=1),
        )
        db_session.add(row)
    await db_session.flush()

    svc = _svc(db_session)
    deleted = await svc.invalidate_for_chunks([10, 20, 30])

    assert deleted == 3

    from sqlalchemy import select

    remaining = (
        await db_session.execute(select(PromptCacheHandle))
    ).scalars().all()
    assert remaining == []


@pytest.mark.asyncio
async def test_invalidate_for_chunks_empty_list_is_noop(db_session: AsyncSession):
    svc = _svc(db_session)
    deleted = await svc.invalidate_for_chunks([])
    assert deleted == 0


# ---------------------------------------------------------------------------
# 5. cleanup_expired
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cleanup_expired_deletes_only_expired_rows(db_session: AsyncSession):
    live = PromptCacheHandle(
        cache_key="live-cleanup",
        gemini_cache_id="caches/live",
        model="gemini-2.0-flash",
        token_count=50,
        expires_at=_now() + timedelta(hours=1),
    )
    expired1 = PromptCacheHandle(
        cache_key="expired-cleanup-1",
        gemini_cache_id="caches/exp1",
        model="gemini-2.0-flash",
        token_count=50,
        expires_at=_now() - timedelta(hours=2),
    )
    expired2 = PromptCacheHandle(
        cache_key="expired-cleanup-2",
        gemini_cache_id="caches/exp2",
        model="gemini-2.0-flash",
        token_count=50,
        expires_at=_now() - timedelta(minutes=1),
    )
    db_session.add_all([live, expired1, expired2])
    await db_session.flush()

    svc = _svc(db_session)
    deleted = await svc.cleanup_expired()

    assert deleted == 2

    from sqlalchemy import select

    remaining = (
        await db_session.execute(select(PromptCacheHandle))
    ).scalars().all()
    assert len(remaining) == 1
    assert remaining[0].cache_key == "live-cleanup"
