# ruff: noqa: UP045, UP017
"""FeatureFlagService — read/write chat_feature_flags with 60s in-process cache (Phase 08).

Hot path (every chat turn) calls `is_enabled('chatbot_public', user_id)` —
cache keeps it free after the first lookup per process. Admin writes bypass
the cache so toggles propagate within `_TTL_SEC` (60s) on next read.
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_TTL_SEC = 60


@dataclass
class _CacheEntry:
    enabled: bool
    rollout_percent: int
    expires_at: float


class FeatureFlagService:
    # Process-wide; safe because the data is small and the writer invalidates.
    _cache: dict[str, _CacheEntry] = {}

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _load(self, flag_key: str) -> _CacheEntry:
        now = time.time()
        cached = self._cache.get(flag_key)
        if cached is not None and cached.expires_at > now:
            return cached
        row = (
            await self.db.execute(
                text(
                    "SELECT enabled, rollout_percent FROM chat_feature_flags "
                    "WHERE flag_key = :k"
                ),
                {"k": flag_key},
            )
        ).first()
        if row is None:
            entry = _CacheEntry(False, 0, now + _TTL_SEC)
        else:
            entry = _CacheEntry(bool(row[0]), int(row[1] or 0), now + _TTL_SEC)
        self._cache[flag_key] = entry
        return entry

    async def is_enabled(
        self, flag_key: str, user_id: Optional[int] = None
    ) -> bool:
        """Master check used by request handlers.

        - flag disabled → False
        - flag enabled, rollout 100 → True
        - flag enabled, rollout <100 → deterministic by hash(flag_key + user_id)
          (anonymous user_id=None is treated as bucket 0 → falls under rollout).
        """
        entry = await self._load(flag_key)
        if not entry.enabled:
            return False
        if entry.rollout_percent >= 100:
            return True
        if entry.rollout_percent <= 0:
            return False
        bucket = _user_bucket(flag_key, user_id)
        return bucket < entry.rollout_percent

    async def set_flag(
        self, flag_key: str, enabled: bool, rollout_percent: int = 0,
        description: Optional[str] = None,
    ) -> None:
        """Admin writer. Invalidates the cache entry so the next read re-fetches."""
        await self.db.execute(
            text(
                """
                INSERT INTO chat_feature_flags (flag_key, enabled, rollout_percent, description)
                VALUES (:k, :e, :r, :d)
                ON CONFLICT (flag_key) DO UPDATE SET
                    enabled = EXCLUDED.enabled,
                    rollout_percent = EXCLUDED.rollout_percent,
                    description = COALESCE(EXCLUDED.description, chat_feature_flags.description),
                    updated_at = CURRENT_TIMESTAMP
                """
            ),
            {"k": flag_key, "e": enabled, "r": rollout_percent, "d": description},
        )
        self._cache.pop(flag_key, None)

    @classmethod
    def invalidate(cls, flag_key: Optional[str] = None) -> None:
        """Drop cache entry (or all entries when key=None). Used by tests."""
        if flag_key is None:
            cls._cache.clear()
        else:
            cls._cache.pop(flag_key, None)


def _user_bucket(flag_key: str, user_id: Optional[int]) -> int:
    """Stable 0-99 bucket per (flag, user)."""
    seed = f"{flag_key}:{user_id or 0}"
    digest = hashlib.sha1(seed.encode()).digest()
    return digest[0] % 100


__all__ = ["FeatureFlagService"]
