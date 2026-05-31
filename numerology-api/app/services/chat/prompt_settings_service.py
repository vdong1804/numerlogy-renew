"""Admin-tunable chat settings (Phase 07) — hybrid override over in-code constant.

Strategy
--------
- `get_override(key)` returns the current DB-stored value for ``key`` or ``None``
  when no override exists. The chat code (prompt_builder) treats ``None`` as
  "use the in-code SYSTEM_PROMPT constant" — keeping Gemini's explicit prompt
  cache stable for the common case.
- `update(key, value, user_id)` upserts the row, appends an audit entry to
  ``chat_system_settings_history``, bumps the version counter and invalidates
  the in-process read cache.
- `delete(key)` removes the override (history retained) so the chat reverts to
  the in-code constant.
- Reads are cached in-process for 60s to avoid hammering the DB on the hot
  chat request path. The cache is global (module-level) but invalidated on
  any local write — across processes the worst case is ``cache_ttl`` of stale
  read which we accept (admin tuning is low-frequency).

The service does NOT touch ``prompt_cache_handles`` directly; the caller
(admin router) decides when to call ``PromptCacheService.invalidate_for_chunks``
after a prompt change since broad invalidation is destructive.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat.system_settings import (
    ChatSystemSetting,
    ChatSystemSettingHistory,
)

logger = logging.getLogger(__name__)

KEY_SYSTEM_PROMPT = "chat_system_prompt"
_CACHE_TTL_SECONDS = 60


class _CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Optional[str], expires_at: float) -> None:
        self.value = value
        self.expires_at = expires_at


_cache: dict[str, _CacheEntry] = {}
_cache_lock = asyncio.Lock()


def _now() -> float:
    return time.monotonic()


def invalidate_cache(key: Optional[str] = None) -> None:
    """Drop one key (or the whole cache) — call from any process after a write."""
    if key is None:
        _cache.clear()
    else:
        _cache.pop(key, None)


class PromptSettingsService:
    """CRUD for ``chat_system_settings`` with audit log + read cache."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_override(self, key: str = KEY_SYSTEM_PROMPT) -> Optional[str]:
        """Return current override value or ``None`` if no row exists."""
        now = _now()
        cached = _cache.get(key)
        if cached is not None and cached.expires_at > now:
            return cached.value

        async with _cache_lock:
            # Re-check inside lock to avoid duplicate DB hits on cache stampede
            cached = _cache.get(key)
            if cached is not None and cached.expires_at > _now():
                return cached.value

            stmt = select(ChatSystemSetting.value).where(
                ChatSystemSetting.key == key
            )
            row = (await self._db.execute(stmt)).scalar_one_or_none()
            _cache[key] = _CacheEntry(row, _now() + _CACHE_TTL_SECONDS)
            return row

    async def get_current(self, key: str = KEY_SYSTEM_PROMPT) -> Optional[ChatSystemSetting]:
        """Return the full row (for admin UI — includes version + updated_at)."""
        stmt = select(ChatSystemSetting).where(ChatSystemSetting.key == key)
        return (await self._db.execute(stmt)).scalar_one_or_none()

    async def update(
        self,
        key: str,
        new_value: str,
        updated_by: Optional[int],
    ) -> ChatSystemSetting:
        """Upsert + snapshot to history. Caller must commit the session.

        Audit semantics: ``changed_by`` is the user *making the change*
        (i.e. the current ``updated_by`` arg). The history row therefore
        captures "version N existed and was about to be replaced by this
        admin." Prior author can be recovered by reading the previous
        history row's ``changed_by``.
        """
        existing = await self.get_current(key)
        if existing is None:
            row = ChatSystemSetting(
                key=key,
                value=new_value,
                updated_by=updated_by,
                version=1,
            )
            self._db.add(row)
            await self._db.flush()
            self._db.add(
                ChatSystemSettingHistory(
                    key=key,
                    value=new_value,
                    version=1,
                    changed_by=updated_by,
                )
            )
        else:
            # Snapshot previous value, attributed to the admin causing the change.
            self._db.add(
                ChatSystemSettingHistory(
                    key=existing.key,
                    value=existing.value,
                    version=existing.version,
                    changed_by=updated_by,
                )
            )
            existing.value = new_value
            existing.updated_by = updated_by
            existing.version = existing.version + 1
            row = existing
        await self._db.flush()
        # Pull server-side onupdate timestamp back into the Python instance so
        # routers can serialise updated_at without triggering a lazy refresh
        # outside the async session greenlet.
        await self._db.refresh(row)
        invalidate_cache(key)
        logger.info(
            "prompt_settings updated key=%s version=%d by user=%s",
            key, row.version, updated_by,
        )
        return row

    async def delete(
        self,
        key: str = KEY_SYSTEM_PROMPT,
        deleted_by: Optional[int] = None,
    ) -> bool:
        """Remove override (history retained). Returns True if a row was deleted.

        ``deleted_by`` is recorded on the final history entry to attribute the
        deletion event; when ``None`` the prior updater is used as a fallback.
        """
        existing = await self.get_current(key)
        if existing is None:
            return False
        self._db.add(
            ChatSystemSettingHistory(
                key=existing.key,
                value=existing.value,
                version=existing.version,
                changed_by=deleted_by if deleted_by is not None else existing.updated_by,
            )
        )
        await self._db.delete(existing)
        await self._db.flush()
        invalidate_cache(key)
        logger.info("prompt_settings deleted key=%s by user=%s", key, deleted_by)
        return True

    async def list_history(
        self, key: str = KEY_SYSTEM_PROMPT, limit: int = 50
    ) -> Sequence[ChatSystemSettingHistory]:
        stmt = (
            select(ChatSystemSettingHistory)
            .where(ChatSystemSettingHistory.key == key)
            .order_by(ChatSystemSettingHistory.changed_at.desc())
            .limit(limit)
        )
        return (await self._db.execute(stmt)).scalars().all()


__all__ = [
    "PromptSettingsService",
    "KEY_SYSTEM_PROMPT",
    "invalidate_cache",
]
