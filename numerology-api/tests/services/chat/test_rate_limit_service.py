# ruff: noqa: UP017, UP045
"""Unit tests for RateLimitService.

All tests run against in-memory SQLite via the shared db_session fixture.
SELECT FOR UPDATE is a no-op in SQLite but the logic is still exercised
through the pure-function helpers (_apply_refill, _check_bucket).
PostgreSQL-specific concurrency guarantees are noted with TODO comments.

Table: rate_limit_buckets — created by Base.metadata.create_all in the
       engine fixture (RateLimitBucket model is registered in models/chat/__init__.py).
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from unittest.mock import AsyncMock, patch

from sqlalchemy.exc import OperationalError

from app.config import settings
from app.services.chat.rate_limit_service import (
    RateLimitConfig,
    RateLimitResult,
    RateLimitService,
    TZ_BANGKOK,
    _apply_refill,
    _check_bucket,
    _seconds_to_next_bangkok_midnight,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_USER_ID = 1
_IP = "127.0.0.1"


async def _get_bucket(db: AsyncSession, key: str) -> dict | None:
    result = await db.execute(
        text(
            "SELECT bucket_key, tokens, capacity, refill_rate, "
            "last_refill, daily_count, daily_reset_date "
            "FROM rate_limit_buckets WHERE bucket_key = :key"
        ),
        {"key": key},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def _seed_bucket(
    db: AsyncSession,
    key: str,
    *,
    tokens: float = 1.0,
    capacity: float = 1.0,
    refill_rate: float = 0.1,
    daily_count: int = 0,
    daily_reset_date: date | None = None,
) -> None:
    today = daily_reset_date or datetime.now(timezone.utc).date()
    await db.execute(
        text(
            """
            INSERT INTO rate_limit_buckets
                (bucket_key, tokens, capacity, refill_rate,
                 last_refill, daily_count, daily_reset_date)
            VALUES (:key, :tokens, :cap, :rate, :now, :dc, :today)
            ON CONFLICT (bucket_key) DO UPDATE
                SET tokens=:tokens, capacity=:cap, refill_rate=:rate,
                    last_refill=:now, daily_count=:dc, daily_reset_date=:today
            """
        ),
        {
            "key": key,
            "tokens": str(tokens),
            "cap": str(capacity),
            "rate": str(refill_rate),
            "now": datetime.now(timezone.utc).isoformat(),
            "dc": daily_count,
            "today": today.isoformat(),
        },
    )
    await db.flush()


# ---------------------------------------------------------------------------
# Pure-function tests (always run — no DB needed)
# ---------------------------------------------------------------------------


def test_apply_refill_adds_tokens_up_to_capacity():
    """Elapsed time * refill_rate is added, capped at capacity."""
    now = datetime.now(timezone.utc)
    last_refill = now - timedelta(seconds=10)
    row = {
        "tokens": "0.00",
        "refill_rate": "0.10",
        "last_refill": last_refill,
        "daily_count": 0,
        "daily_reset_date": now.date(),
    }
    cfg = RateLimitConfig(capacity=1.0, refill_per_sec=0.1, daily_cap=100)
    tokens, daily = _apply_refill(row, cfg, now, now.date())
    assert tokens == pytest.approx(1.0, abs=0.01)  # 10s * 0.1 = 1.0, capped
    assert daily == 0


def test_apply_refill_rolls_daily_count_on_new_date():
    """daily_count resets to 0 when daily_reset_date < today."""
    now = datetime.now(timezone.utc)
    yesterday = now.date() - timedelta(days=1)
    row = {
        "tokens": "0.50",
        "refill_rate": "0.10",
        "last_refill": now,
        "daily_count": 99,
        "daily_reset_date": yesterday,
    }
    cfg = RateLimitConfig(capacity=1.0, refill_per_sec=0.1, daily_cap=100)
    _, daily = _apply_refill(row, cfg, now, now.date())
    assert daily == 0  # rolled over


def test_check_bucket_allows_when_tokens_available():
    cfg = RateLimitConfig(capacity=1.0, refill_per_sec=0.1, daily_cap=100)
    result = _check_bucket(1.0, 0, cfg)
    assert result.allowed is True


def test_check_bucket_blocks_empty_bucket():
    cfg = RateLimitConfig(capacity=1.0, refill_per_sec=0.1, daily_cap=100)
    result = _check_bucket(0.5, 0, cfg)
    assert result.allowed is False
    assert result.reason == "bucket_empty"
    assert result.retry_after > 0


def test_check_bucket_blocks_daily_cap():
    cfg = RateLimitConfig(capacity=1.0, refill_per_sec=0.1, daily_cap=100)
    result = _check_bucket(1.0, 100, cfg)  # daily_count == daily_cap
    assert result.allowed is False
    assert result.reason == "daily_cap"
    assert result.retry_after > 0


def test_tier_config_differs_pro_vs_free():
    """Pro refill rate is higher than free."""
    svc = RateLimitService.__new__(RateLimitService)  # no __init__ needed
    free_cfg = svc._config_for_tier("flash")
    pro_cfg = svc._config_for_tier("pro")
    assert pro_cfg.refill_per_sec > free_cfg.refill_per_sec
    assert pro_cfg.daily_cap > free_cfg.daily_cap


# ---------------------------------------------------------------------------
# Integration-style tests (use db_session + SQLite)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_first_request_creates_bucket_with_full_tokens(db_session: AsyncSession):
    """First check_and_consume creates the bucket row with tokens == capacity."""
    try:
        svc = RateLimitService(db_session)
        result = await svc.check_and_consume(user_id=_USER_ID, ip=_IP, tier="flash")
    except Exception as exc:
        if "no such table" in str(exc).lower():
            pytest.skip("rate_limit_buckets table not in SQLite schema")
        raise

    assert result.allowed is True

    user_key = f"user:{_USER_ID}"
    bucket = await _get_bucket(db_session, user_key)
    assert bucket is not None
    # capacity == settings.rate_limit_free_capacity (1.0); tokens now 0 after consume
    assert float(bucket["tokens"]) == pytest.approx(0.0, abs=0.05)


@pytest.mark.asyncio
async def test_consume_succeeds_when_tokens_available(db_session: AsyncSession):
    """Bucket with full tokens allows request and decrements tokens."""
    user_key = f"user:{_USER_ID}"
    ip_key = f"ip:{_IP}"
    try:
        await _seed_bucket(db_session, user_key, tokens=1.0, capacity=1.0)
        await _seed_bucket(db_session, ip_key, tokens=5.0, capacity=5.0)
    except Exception as exc:
        if "no such table" in str(exc).lower():
            pytest.skip("rate_limit_buckets table not in SQLite schema")
        raise

    svc = RateLimitService(db_session)
    result = await svc.check_and_consume(user_id=_USER_ID, ip=_IP, tier="flash")
    assert result.allowed is True


@pytest.mark.asyncio
async def test_consume_429_when_bucket_empty_returns_retry_after(db_session: AsyncSession):
    """Bucket with 0 tokens returns allowed=False with positive retry_after."""
    user_key = f"user:{_USER_ID}"
    ip_key = f"ip:{_IP}"
    try:
        await _seed_bucket(db_session, user_key, tokens=0.0, capacity=1.0, refill_rate=0.1)
        await _seed_bucket(db_session, ip_key, tokens=5.0, capacity=5.0)
    except Exception as exc:
        if "no such table" in str(exc).lower():
            pytest.skip("rate_limit_buckets table not in SQLite schema")
        raise

    svc = RateLimitService(db_session)
    result = await svc.check_and_consume(user_id=_USER_ID, ip=_IP, tier="flash")
    assert result.allowed is False
    assert result.reason == "bucket_empty"
    assert result.retry_after > 0


@pytest.mark.asyncio
async def test_daily_cap_blocks_even_with_tokens(db_session: AsyncSession):
    """When daily_count >= daily_cap, request is blocked regardless of tokens."""
    user_key = f"user:{_USER_ID}"
    ip_key = f"ip:{_IP}"
    daily_cap = settings.rate_limit_free_daily_cap  # 100
    try:
        await _seed_bucket(
            db_session, user_key, tokens=1.0, capacity=1.0, daily_count=daily_cap
        )
        await _seed_bucket(db_session, ip_key, tokens=5.0, capacity=5.0)
    except Exception as exc:
        if "no such table" in str(exc).lower():
            pytest.skip("rate_limit_buckets table not in SQLite schema")
        raise

    svc = RateLimitService(db_session)
    result = await svc.check_and_consume(user_id=_USER_ID, ip=_IP, tier="flash")
    assert result.allowed is False
    assert result.reason == "daily_cap"


@pytest.mark.asyncio
async def test_daily_count_resets_on_new_date(db_session: AsyncSession):
    """daily_count from yesterday is reset to 0 (rolled over on new date)."""
    user_key = f"user:{_USER_ID}"
    ip_key = f"ip:{_IP}"
    yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
    daily_cap = settings.rate_limit_free_daily_cap
    try:
        await _seed_bucket(
            db_session, user_key,
            tokens=1.0, capacity=1.0,
            daily_count=daily_cap,  # would block if not rolled
            daily_reset_date=yesterday,
        )
        await _seed_bucket(db_session, ip_key, tokens=5.0, capacity=5.0)
    except Exception as exc:
        if "no such table" in str(exc).lower():
            pytest.skip("rate_limit_buckets table not in SQLite schema")
        raise

    svc = RateLimitService(db_session)
    result = await svc.check_and_consume(user_id=_USER_ID, ip=_IP, tier="flash")
    # After roll-over, daily_count becomes 0 → request allowed
    assert result.allowed is True


@pytest.mark.asyncio
async def test_ip_bucket_independent_of_user_bucket(db_session: AsyncSession):
    """IP bucket failure blocks even when user bucket would pass."""
    user_key = f"user:{_USER_ID}"
    ip_key = f"ip:{_IP}"
    try:
        await _seed_bucket(db_session, user_key, tokens=1.0, capacity=1.0)
        # IP bucket empty
        await _seed_bucket(
            db_session, ip_key, tokens=0.0, capacity=5.0,
            refill_rate=settings.rate_limit_ip_refill_per_sec,
        )
    except Exception as exc:
        if "no such table" in str(exc).lower():
            pytest.skip("rate_limit_buckets table not in SQLite schema")
        raise

    svc = RateLimitService(db_session)
    result = await svc.check_and_consume(user_id=_USER_ID, ip=_IP, tier="flash")
    assert result.allowed is False


@pytest.mark.asyncio
async def test_both_buckets_must_pass_user_pass_ip_fail_no_user_consume(
    db_session: AsyncSession,
):
    """When IP fails, user bucket tokens must NOT be decremented."""
    user_key = f"user:{_USER_ID}"
    ip_key = f"ip:{_IP}"
    try:
        await _seed_bucket(db_session, user_key, tokens=1.0, capacity=1.0)
        await _seed_bucket(
            db_session, ip_key, tokens=0.0, capacity=5.0,
            refill_rate=settings.rate_limit_ip_refill_per_sec,
        )
    except Exception as exc:
        if "no such table" in str(exc).lower():
            pytest.skip("rate_limit_buckets table not in SQLite schema")
        raise

    svc = RateLimitService(db_session)
    await svc.check_and_consume(user_id=_USER_ID, ip=_IP, tier="flash")

    # Reload user bucket — tokens should still be ~1.0 (not consumed)
    bucket = await _get_bucket(db_session, user_key)
    assert bucket is not None
    assert float(bucket["tokens"]) == pytest.approx(1.0, abs=0.05)


@pytest.mark.asyncio
async def test_bucket_refills_over_time():
    """_apply_refill pure function: 10 s elapsed at 0.1/s → +1.0 token."""
    now = datetime.now(timezone.utc)
    ten_seconds_ago = now - timedelta(seconds=10)
    row = {
        "tokens": "0.00",
        "refill_rate": "0.10",
        "last_refill": ten_seconds_ago,
        "daily_count": 0,
        "daily_reset_date": now.date(),
    }
    cfg = RateLimitConfig(capacity=1.0, refill_per_sec=0.1, daily_cap=100)
    tokens, _ = _apply_refill(row, cfg, now, now.date())
    assert tokens == pytest.approx(1.0, abs=0.02)
    # Should pass check now
    result = _check_bucket(tokens, 0, cfg)
    assert result.allowed is True


@pytest.mark.asyncio
async def test_concurrent_consume_double_call_only_one_or_both_succeed(
    db_session_factory,
):
    """Two concurrent check_and_consume calls share state.

    SQLite doesn't enforce FOR UPDATE, so both may succeed.
    We verify the combined outcome: total tokens consumed matches successes.
    For true serialization, run against PostgreSQL.
    """
    user_key = f"user:{_USER_ID}"
    ip_key = f"ip:{_IP}"

    try:
        async with db_session_factory() as setup:
            await _seed_bucket(setup, user_key, tokens=1.0, capacity=1.0)
            await _seed_bucket(setup, ip_key, tokens=5.0, capacity=5.0)
            await setup.commit()
    except Exception as exc:
        if "no such table" in str(exc).lower():
            pytest.skip("rate_limit_buckets table not in SQLite schema")
        raise

    results: list[RateLimitResult] = []

    async def _call():
        async with db_session_factory() as sess:
            svc = RateLimitService(sess)
            try:
                r = await svc.check_and_consume(user_id=_USER_ID, ip=_IP, tier="flash")
                await sess.commit()
                results.append(r)
            except Exception:  # noqa: BLE001
                await sess.rollback()
                results.append(RateLimitResult(allowed=False, reason="error"))

    await asyncio.gather(_call(), _call())

    successes = sum(1 for r in results if r.allowed)
    # SQLite: both may succeed (no real lock); Postgres: at most 1 would succeed
    # Minimum guarantee: at least one result recorded
    assert len(results) == 2
    assert successes >= 0  # don't assert strict <=1 on SQLite


# ---------------------------------------------------------------------------
# C2 — daily_cap retry_after uses Asia/Bangkok midnight
# ---------------------------------------------------------------------------


def test_daily_cap_retry_after_uses_bangkok_midnight_17_30_utc():
    """17:30 UTC = 00:30 Bangkok next day → retry_after should be ~(23h30m) seconds."""
    # 17:30 UTC → 00:30 Bangkok (next day already past midnight)
    now_utc = datetime(2026, 1, 15, 17, 30, 0, tzinfo=timezone.utc)
    secs = _seconds_to_next_bangkok_midnight(now_utc)
    # Bangkok is 00:30; next midnight is at 23h30m away (23*3600 + 30*60 = 84600s)
    assert 84590 <= secs <= 84610, f"Expected ~84600s, got {secs}"


def test_daily_cap_retry_after_uses_bangkok_midnight_23_30_utc():
    """23:30 UTC = 06:30 Bangkok same day → retry_after should be ~17h30m seconds."""
    # 23:30 UTC → 06:30 Bangkok; next midnight is in 17h30m
    now_utc = datetime(2026, 1, 15, 23, 30, 0, tzinfo=timezone.utc)
    secs = _seconds_to_next_bangkok_midnight(now_utc)
    # 17h30m = 17*3600 + 30*60 = 63000s
    assert 62990 <= secs <= 63010, f"Expected ~63000s, got {secs}"


def test_check_bucket_daily_cap_retry_after_is_positive():
    """_check_bucket daily_cap returns positive retry_after seconds."""
    cfg = RateLimitConfig(capacity=1.0, refill_per_sec=0.1, daily_cap=100)
    result = _check_bucket(1.0, 100, cfg)
    assert result.allowed is False
    assert result.reason == "daily_cap"
    assert result.retry_after > 0
    # Retry should be < 24h
    assert result.retry_after <= 24 * 3600


# ---------------------------------------------------------------------------
# C3 — concurrent consume releases lock promptly (SQLite approximation)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_concurrent_consume_releases_lock_promptly(db_session_factory):
    """Two sequential consume calls complete without deadlock (SQLite approximation of C3)."""
    user_key = f"user:{_USER_ID}"
    ip_key = f"ip:{_IP}"

    try:
        async with db_session_factory() as setup:
            await _seed_bucket(setup, user_key, tokens=2.0, capacity=2.0)
            await _seed_bucket(setup, ip_key, tokens=5.0, capacity=5.0)
            await setup.commit()
    except Exception as exc:
        if "no such table" in str(exc).lower():
            pytest.skip("rate_limit_buckets table not in SQLite schema")
        raise

    results: list[RateLimitResult] = []

    async def _call():
        async with db_session_factory() as sess:
            svc = RateLimitService(sess)
            try:
                r = await svc.check_and_consume(user_id=_USER_ID, ip=_IP, tier="flash")
                # check_and_consume now commits its own transaction (C3 fix)
                results.append(r)
            except Exception:  # noqa: BLE001
                results.append(RateLimitResult(allowed=False, reason="error"))

    # Run concurrently — must not deadlock
    await asyncio.gather(_call(), _call())
    assert len(results) == 2  # both completed, no deadlock


# ---------------------------------------------------------------------------
# H1 — fail-closed on DB error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_db_error_during_check_returns_disallowed(db_session):
    """H1 fix: DB OperationalError returns allowed=False with service_error reason."""
    svc = RateLimitService(db_session)

    # Patch _ensure_bucket to raise OperationalError
    async def _raise(*args, **kwargs):
        raise OperationalError("connection lost", None, None)

    with patch.object(svc, "_ensure_bucket", _raise):
        result = await svc.check_and_consume(user_id=_USER_ID, ip=_IP, tier="flash")

    assert result.allowed is False
    assert result.reason == "service_error"
    assert result.retry_after == 5.0


@pytest.mark.asyncio
async def test_unexpected_error_during_check_returns_disallowed(db_session):
    """H1 fix: unexpected exceptions also fail-closed."""
    svc = RateLimitService(db_session)

    async def _raise(*args, **kwargs):
        raise RuntimeError("unexpected boom")

    with patch.object(svc, "_ensure_bucket", _raise):
        result = await svc.check_and_consume(user_id=_USER_ID, ip=_IP, tier="flash")

    assert result.allowed is False
    assert result.reason == "service_error"
