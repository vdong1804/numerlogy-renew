# ruff: noqa: UP017  — datetime.UTC is Python 3.11+; runtime is 3.9
"""QuotaService — enforces per-user chat message limits.

Resolution order:
  1. Active add-on (is_active=True, expires_at > NOW(), remaining_messages > 0)
     → tier from addon row, source="addon"
  2. Free daily quota (chat_quota_usage.free_used < settings.chat_free_daily_limit)
     → tier="flash", source="free"
  3. Quota exhausted → can_send=False, reason="quota_exceeded"

decrement() must be called AFTER a successful LLM response to avoid charging
for failed turns. Uses SELECT FOR UPDATE on the addon row to prevent race
conditions when multiple concurrent requests share the same addon.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Literal

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.chat.chat_addon_purchase import ChatAddonPurchase
from app.db.models.chat.quota_usage import ChatQuotaUsage

# ---------------------------------------------------------------------------
# Public data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class QuotaDecision:
    can_send: bool
    tier: Literal["flash", "pro"] | None = None
    source: Literal["addon", "free"] | None = None
    addon_id: int | None = None
    free_remaining: int | None = None
    reason: str | None = None


@dataclass(frozen=True)
class QuotaBalance:
    free_used_today: int
    free_limit: int
    addon_remaining: int          # 0 when no active addon
    addon_tier: str | None
    addon_expires_at: datetime | None


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class QuotaConflictError(RuntimeError):
    """Raised when addon balance hit 0 between check() and decrement()."""


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


class QuotaService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # peek_tier — cheap read-only tier resolution for rate-limit pre-check
    # ------------------------------------------------------------------

    async def peek_tier(self, user_id: int) -> str:
        """Return tier without full quota validation — used by rate-limit check (H6 fix).

        Returns "pro" when user has an active addon with remaining messages,
        else "free". No writes, no expiry side effects.
        """
        addon = await self._get_active_addon(user_id)
        if addon is not None:
            return addon.tier or "free"
        return "free"

    # ------------------------------------------------------------------
    # check — read-only, never writes
    # ------------------------------------------------------------------

    async def check(self, user_id: int) -> QuotaDecision:
        """Determine whether user may send a message and which tier to use."""
        # 1. Active add-on with messages remaining
        addon = await self._get_active_addon(user_id)
        if addon is not None:
            return QuotaDecision(
                can_send=True,
                tier=addon.tier,  # type: ignore[arg-type]
                source="addon",
                addon_id=addon.id,
            )

        # 2. Free daily quota
        free_used = await self._get_free_used_today(user_id)
        limit: int = settings.chat_free_daily_limit
        if free_used < limit:
            return QuotaDecision(
                can_send=True,
                tier="flash",
                source="free",
                free_remaining=limit - free_used,
            )

        # 3. Exhausted
        return QuotaDecision(can_send=False, reason="quota_exceeded")

    # ------------------------------------------------------------------
    # decrement — writes; call only after successful LLM response
    # ------------------------------------------------------------------

    async def decrement(self, user_id: int, decision: QuotaDecision) -> None:
        """Apply usage from *decision* (previously returned by check())."""
        if not decision.can_send:
            return  # nothing to decrement on a blocked decision

        if decision.source == "addon":
            await self._decrement_addon(decision.addon_id)  # type: ignore[arg-type]
        elif decision.source == "free":
            await self._increment_free_used(user_id)

    # ------------------------------------------------------------------
    # get_balance — read-only summary for UI badge / quota endpoint
    # ------------------------------------------------------------------

    async def get_balance(self, user_id: int) -> QuotaBalance:
        """Return current quota state for the user."""
        free_used = await self._get_free_used_today(user_id)
        addon = await self._get_active_addon(user_id)
        return QuotaBalance(
            free_used_today=free_used,
            free_limit=settings.chat_free_daily_limit,
            addon_remaining=addon.remaining_messages if addon else 0,
            addon_tier=addon.tier if addon else None,
            addon_expires_at=addon.expires_at if addon else None,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get_active_addon(self, user_id: int) -> ChatAddonPurchase | None:
        """Most-recently-purchased active add-on with messages remaining."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(ChatAddonPurchase)
            .where(
                ChatAddonPurchase.user_id == user_id,
                ChatAddonPurchase.is_active.is_(True),
                ChatAddonPurchase.expires_at > now,
                ChatAddonPurchase.remaining_messages > 0,
            )
            .order_by(ChatAddonPurchase.purchased_at.desc())
            .limit(1)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_free_used_today(self, user_id: int) -> int:
        """Return free_used count for today (UTC). Returns 0 if no row yet."""
        today = _utc_today()
        stmt = select(ChatQuotaUsage).where(
            ChatQuotaUsage.user_id == user_id,
            ChatQuotaUsage.date == today,
        )
        result = await self._db.execute(stmt)
        row = result.scalar_one_or_none()
        return row.free_used if row is not None else 0

    async def _decrement_addon(self, addon_id: int) -> None:
        """Decrement remaining_messages with SELECT FOR UPDATE (race-safe).

        Also validates expires_at > NOW() to reject decrements against an addon
        that expired mid-stream (e.g. during a long LLM call).
        """
        stmt = (
            select(ChatAddonPurchase)
            .where(ChatAddonPurchase.id == addon_id)
            .with_for_update()
        )
        result = await self._db.execute(stmt)
        addon = result.scalar_one_or_none()

        if addon is None or addon.remaining_messages <= 0:
            raise QuotaConflictError(
                f"Addon {addon_id} has no messages left at decrement time (race condition)."
            )

        now = datetime.now(timezone.utc)
        if addon.expires_at is not None:
            # Normalise to aware datetime for comparison (SQLite returns naive)
            expires = (
                addon.expires_at
                if addon.expires_at.tzinfo is not None
                else addon.expires_at.replace(tzinfo=timezone.utc)
            )
            if expires <= now:
                raise QuotaConflictError(
                    f"Addon {addon_id} expired at {addon.expires_at} before decrement."
                )

        addon.remaining_messages -= 1
        if addon.remaining_messages == 0:
            addon.is_active = False
        await self._db.flush()

    async def _increment_free_used(self, user_id: int) -> None:
        """Atomic upsert: INSERT … ON CONFLICT DO UPDATE SET free_used = free_used + 1."""
        today = _utc_today()
        await self._db.execute(
            text(
                """
                INSERT INTO chat_quota_usage (user_id, date, free_used, paid_used)
                VALUES (:uid, :today, 1, 0)
                ON CONFLICT (user_id, date)
                DO UPDATE SET free_used = chat_quota_usage.free_used + 1
                """
            ),
            {"uid": user_id, "today": today},
        )
        await self._db.flush()
