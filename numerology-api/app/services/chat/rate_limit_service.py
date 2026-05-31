# ruff: noqa: UP045, UP017
"""RateLimitService — token-bucket rate limiting per (user_id, IP) using DB row locks.

Algorithm per bucket:
  1. SELECT ... FOR UPDATE (create row if absent via INSERT ON CONFLICT DO NOTHING).
  2. Compute refill: elapsed_seconds * refill_rate, capped at capacity.
  3. Roll daily counter if daily_reset_date < today (Asia/Bangkok local date).
  4. Check: tokens >= 1 AND daily_count < daily_cap.
  5. If both buckets pass: deduct 1 token + increment daily_count on BOTH, COMMIT.
  6. If either fails: return RateLimitResult(allowed=False, ...).

Daily cap resets at Asia/Bangkok (UTC+7) midnight — users in VN see correct 00:00 rollover.
Using two buckets (user + IP) in a single transaction avoids partial consumption.
Move to Redis if sustained RPS exceeds ~100 (DB lock contention becomes the bottleneck).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

# Daily caps reset at Bangkok midnight (UTC+7) — visible to Vietnamese users as 00:00 local.
TZ_BANGKOK = timezone(timedelta(hours=7))

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RateLimitConfig:
    capacity: float
    refill_per_sec: float
    daily_cap: int


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    retry_after: float = 0.0   # seconds; set Retry-After header to this value
    reason: Optional[str] = None  # "bucket_empty" | "daily_cap"


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------


class RateLimitExceeded(RuntimeError):
    """Raised internally; caller maps to HTTP 429."""

    def __init__(self, result: RateLimitResult) -> None:
        self.result = result
        super().__init__(result.reason)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class RateLimitService:
    """Token-bucket rate limiter backed by PostgreSQL row-level locks."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def check_and_consume(
        self, *, user_id: int, ip: str, tier: str
    ) -> RateLimitResult:
        """Check both user and IP buckets; consume from both only if both pass.

        Returns RateLimitResult(allowed=True) on success.
        Returns RateLimitResult(allowed=False, ...) when rate-limited.
        Never raises — callers inspect the result.
        """
        user_key = f"user:{user_id}"
        ip_key = f"ip:{ip}"
        user_cfg = self._config_for_tier(tier)
        ip_cfg = self._ip_config()

        try:
            # Ensure both bucket rows exist before locking
            await self._ensure_bucket(user_key, user_cfg)
            await self._ensure_bucket(ip_key, ip_cfg)

            # Lock both rows, compute decisions, commit atomically
            result = await self._transact(user_key, user_cfg, ip_key, ip_cfg)
            return result
        except (OperationalError, SQLAlchemyError) as exc:
            # Fail-CLOSED: DB issues block all chat to prevent unbounded abuse.
            # Returns 429 (not 503) per KISS — spec doesn't differentiate.
            logger.error("rate_limit DB error for user=%s ip=%s: %s", user_id, ip, exc)
            return RateLimitResult(allowed=False, retry_after=5.0, reason="service_error")
        except Exception as exc:  # noqa: BLE001
            # Fail-CLOSED: unknown errors also block to prevent bypass via poisoned rows.
            logger.error("rate_limit unexpected error for user=%s ip=%s: %s", user_id, ip, exc)
            return RateLimitResult(allowed=False, retry_after=5.0, reason="service_error")

    # ------------------------------------------------------------------
    # Tier config
    # ------------------------------------------------------------------

    def _config_for_tier(self, tier: str) -> RateLimitConfig:
        if tier == "pro":
            return RateLimitConfig(
                capacity=settings.rate_limit_pro_capacity,
                refill_per_sec=settings.rate_limit_pro_refill_per_sec,
                daily_cap=settings.rate_limit_pro_daily_cap,
            )
        # Default: free
        return RateLimitConfig(
            capacity=settings.rate_limit_free_capacity,
            refill_per_sec=settings.rate_limit_free_refill_per_sec,
            daily_cap=settings.rate_limit_free_daily_cap,
        )

    def _ip_config(self) -> RateLimitConfig:
        return RateLimitConfig(
            capacity=settings.rate_limit_ip_capacity,
            refill_per_sec=settings.rate_limit_ip_refill_per_sec,
            daily_cap=settings.rate_limit_ip_daily_cap,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _ensure_bucket(self, key: str, cfg: RateLimitConfig) -> None:
        """Insert bucket row with full tokens if it doesn't exist yet."""
        now = datetime.now(timezone.utc)
        today = now.astimezone(TZ_BANGKOK).date()  # Bangkok local date for daily reset
        sql = text(
            """
            INSERT INTO rate_limit_buckets
                (bucket_key, tokens, capacity, refill_rate, last_refill,
                 daily_count, daily_reset_date)
            VALUES (
                :key,
                :capacity,
                :capacity,
                :refill_rate,
                :now,
                0,
                :today
            )
            ON CONFLICT (bucket_key) DO NOTHING
            """
        )
        await self._db.execute(
            sql,
            {
                "key": key,
                "capacity": str(cfg.capacity),
                "refill_rate": str(cfg.refill_per_sec),
                "now": now,
                "today": today,
            },
        )
        await self._db.flush()

    async def _transact(
        self,
        user_key: str,
        user_cfg: RateLimitConfig,
        ip_key: str,
        ip_cfg: RateLimitConfig,
    ) -> RateLimitResult:
        """Lock both rows, compute, and either update both or leave unchanged.

        Commits its own transaction to release the SELECT FOR UPDATE row lock
        BEFORE returning to the caller (which will proceed to the LLM call).
        Holding the lock during a 5-30s LLM call would exhaust the DB pool.
        """
        now = datetime.now(timezone.utc)
        # Use Bangkok local date for daily rollover — users see 00:00 local reset.
        today = now.astimezone(TZ_BANGKOK).date()

        user_row = await self._lock_row(user_key)
        ip_row = await self._lock_row(ip_key)

        # Compute new state for each bucket (refill + daily roll)
        user_tokens, user_daily = _apply_refill(user_row, user_cfg, now, today)
        ip_tokens, ip_daily = _apply_refill(ip_row, ip_cfg, now, today)

        # Decision — check both before touching any rows
        user_result = _check_bucket(user_tokens, user_daily, user_cfg)
        ip_result = _check_bucket(ip_tokens, ip_daily, ip_cfg)

        if not user_result.allowed:
            # No rows modified — commit to release any implicit lock, return early.
            await self._db.commit()
            return user_result

        if not ip_result.allowed:
            # User passed but IP failed — do NOT update user row (no partial consume)
            await self._db.commit()
            return ip_result

        # Both pass — consume 1 token from each atomically
        await self._update_row(user_key, user_tokens - 1, user_cfg, now, today, user_daily + 1)
        await self._update_row(ip_key, ip_tokens - 1, ip_cfg, now, today, ip_daily + 1)
        # Commit immediately to release FOR UPDATE row lock before LLM call (C3 fix).
        await self._db.commit()
        return RateLimitResult(allowed=True)

    def _is_postgres(self) -> bool:
        """True when the session is connected to PostgreSQL."""
        bind = self._db.get_bind()
        return bind is not None and "postgresql" in str(bind.dialect.name).lower()

    async def _lock_row(self, key: str) -> dict:
        """SELECT (FOR UPDATE on Postgres only) the bucket row; returns a plain dict.

        SQLite used in tests does not support FOR UPDATE; we omit it there.
        True serialization only guaranteed on PostgreSQL.
        """
        for_update_clause = "FOR UPDATE" if self._is_postgres() else ""
        sql = text(
            f"""
            SELECT bucket_key, tokens, capacity, refill_rate,
                   last_refill, daily_count, daily_reset_date
            FROM rate_limit_buckets
            WHERE bucket_key = :key
            {for_update_clause}
            """
        )
        result = await self._db.execute(sql, {"key": key})
        row = result.mappings().one()
        return dict(row)

    async def _update_row(
        self,
        key: str,
        new_tokens: float,
        cfg: RateLimitConfig,
        now: datetime,
        today: date,
        new_daily: int,
    ) -> None:
        sql = text(
            """
            UPDATE rate_limit_buckets
            SET tokens           = :tokens,
                last_refill      = :now,
                daily_count      = :daily_count,
                daily_reset_date = :today
            WHERE bucket_key = :key
            """
        )
        await self._db.execute(
            sql,
            {
                "tokens": str(round(new_tokens, 2)),
                "now": now,
                "daily_count": new_daily,
                "today": today,
                "key": key,
            },
        )


# ---------------------------------------------------------------------------
# Pure functions (easier to test)
# ---------------------------------------------------------------------------


def _apply_refill(
    row: dict, cfg: RateLimitConfig, now: datetime, today: date
) -> tuple[float, int]:
    """Return (new_tokens, new_daily_count) after applying refill and daily roll.

    `today` should be the Asia/Bangkok local date (UTC+7) for correct daily rollover.
    """
    last_refill = row["last_refill"]
    # SQLite may return last_refill as a string; parse it to datetime.
    if isinstance(last_refill, str):
        # Strip trailing microseconds variance; isoformat with/without tz
        last_refill = datetime.fromisoformat(last_refill.replace("Z", "+00:00"))
    # Normalise to aware datetime (SQLite returns naive)
    if last_refill.tzinfo is None:
        last_refill = last_refill.replace(tzinfo=timezone.utc)

    elapsed = max(0.0, (now - last_refill).total_seconds())
    tokens = float(row["tokens"]) + elapsed * cfg.refill_per_sec
    tokens = min(tokens, cfg.capacity)

    daily_count: int = int(row["daily_count"])
    reset_date = row["daily_reset_date"]
    # daily_reset_date may come back as date or string depending on driver
    if isinstance(reset_date, str):
        reset_date = date.fromisoformat(reset_date)

    if reset_date < today:
        daily_count = 0

    return tokens, daily_count


def _seconds_to_next_bangkok_midnight(now_utc: datetime) -> int:
    """Seconds until next 00:00 Asia/Bangkok (UTC+7) from the given UTC datetime."""
    now_local = now_utc.astimezone(TZ_BANGKOK)
    next_midnight_local = (now_local + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return int(math.ceil((next_midnight_local - now_local).total_seconds()))


def _check_bucket(tokens: float, daily_count: int, cfg: RateLimitConfig) -> RateLimitResult:
    """Determine if this bucket allows the request."""
    if tokens < 1.0:
        retry = math.ceil((1.0 - tokens) / cfg.refill_per_sec)
        return RateLimitResult(allowed=False, retry_after=float(retry), reason="bucket_empty")

    if daily_count >= cfg.daily_cap:
        # Retry after next Asia/Bangkok midnight — matches the daily rollover TZ (C2 fix).
        now = datetime.now(timezone.utc)
        retry = _seconds_to_next_bangkok_midnight(now)
        return RateLimitResult(allowed=False, retry_after=float(retry), reason="daily_cap")

    return RateLimitResult(allowed=True)
