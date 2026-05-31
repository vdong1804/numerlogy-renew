# ruff: noqa: UP045, UP017, UP035, UP006
"""Gemini explicit prompt-cache lifecycle.

Strategy
--------
cache_key = sha256(system_prompt + "|".join(sorted(str(c) for c in kb_chunk_ids)) + tier)[:64]

get_live_handle(cache_key)
    Fast DB lookup; returns PromptCacheResult if row exists and not expired.
    On hit: refreshes expires_at (now + ttl) to keep hot keys alive.

maybe_create(cache_key, system, kb_chunks, tier, model)
    Lazy creation avoids one-shot waste:
      1. Increment in-process hit counter for cache_key.
      2. If counter < settings.prompt_cache_hit_threshold → return None.
      3. Else call Gemini caches.create() via asyncio.to_thread (sync SDK).
      4. INSERT PromptCacheHandle row; reset counter.
    Hit counter is in-process (not persistent). After a restart the counter
    resets to 0, delaying cache creation by threshold requests — acceptable
    trade-off (lazy creation just means a few un-cached requests post-restart).

invalidate_for_chunks(chunk_ids)  [async]
    BROAD-STROKES strategy: DELETE ALL handles when any KB chunk changes.
    Rationale: cache_key encodes sorted chunk ids but we have no reverse index
    to find which handles reference a specific chunk without adding a JSONB
    column to the handle table. Broad-strokes is safe and correct; 1h TTL
    limits the blast radius. TODO Phase 08: add chunk_ids JSONB to handle
    and implement fine-grained lookup if broad invalidation proves costly.

invalidate_for_chunks_sync(session, chunk_ids)  [sync helper for kb_sync listener]
    Same semantics but uses a synchronous SQLAlchemy Session for use inside
    after_commit event listeners that run in a sync context.

cleanup_expired()
    DELETE WHERE expires_at < NOW() — intended for nightly job.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Callable, List, Optional

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-process hit counter (best-effort; resets on restart)
# ---------------------------------------------------------------------------

_hit_counts: dict[str, int] = defaultdict(int)
_hit_lock = Lock()


class _HitCounter:
    """Thread-safe in-process counter for cache-key hit tracking."""

    @staticmethod
    def increment(key: str) -> int:
        with _hit_lock:
            _hit_counts[key] += 1
            return _hit_counts[key]

    @staticmethod
    def reset(key: str) -> None:
        with _hit_lock:
            _hit_counts.pop(key, None)

    @staticmethod
    def get(key: str) -> int:
        with _hit_lock:
            return _hit_counts.get(key, 0)


# ---------------------------------------------------------------------------
# Public data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PromptCacheResult:
    """Returned by get_live_handle / maybe_create to caller (e.g., LlmService)."""

    gemini_cache_id: Optional[str]   # pass as cached_content= to generate_content
    handle_id: Optional[int]


# ---------------------------------------------------------------------------
# Sync invalidation helper — called from kb_sync after_commit listener
# ---------------------------------------------------------------------------


def invalidate_for_chunks_sync(session: Session, chunk_ids: List[int]) -> int:  # noqa: ARG001
    """Delete ALL prompt cache handles (broad-strokes) when KB chunks change.

    Broad-strokes trade-off: we lack a reverse index from handle → chunk_ids,
    so we nuke every handle on any KB change. With a 1h TTL this means at most
    1h of stale cache data is eliminated early. Fine-grained per-chunk
    invalidation is deferred to Phase 08.
    chunk_ids param kept for API consistency; currently unused in the DELETE.
    """
    if not chunk_ids:
        return 0
    try:
        result = session.execute(text("DELETE FROM prompt_cache_handles"))
        deleted = result.rowcount or 0
        logger.info(
            "prompt_cache invalidated %d handles (broad-strokes, triggered by %d chunk changes)",
            deleted,
            len(chunk_ids),
        )
        return deleted
    except Exception:  # noqa: BLE001
        logger.exception("prompt_cache sync invalidation failed; ignoring")
        return 0


# ---------------------------------------------------------------------------
# PromptCacheService
# ---------------------------------------------------------------------------


class PromptCacheService:
    """Gemini explicit prompt-cache lifecycle (create / lookup / invalidate / cleanup)."""

    def __init__(
        self,
        db: AsyncSession,
        client_provider: Callable[[], object],  # () -> genai.Client; avoids import cycle
    ) -> None:
        self._db = db
        self._client_provider = client_provider

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @staticmethod
    def compute_key(system: str, kb_chunk_ids: List[int], tier: str) -> str:
        """Deterministic 64-char hex key from system prompt + sorted chunk ids + tier."""
        chunk_part = "|".join(str(c) for c in sorted(kb_chunk_ids))
        raw = f"{system}\x00{chunk_part}\x00{tier}"
        return hashlib.sha256(raw.encode()).hexdigest()[:64]

    async def get_live_handle(self, cache_key: str) -> Optional[PromptCacheResult]:
        """Return a live (non-expired) handle and refresh its TTL on hit."""
        # Lazy import — model may not exist until other agent delivers it
        try:
            from app.db.models.chat.prompt_cache_handle import PromptCacheHandle
        except ImportError:
            logger.debug("PromptCacheHandle model not yet available; skipping cache lookup")
            return None

        now = datetime.now(timezone.utc)
        stmt = (
            select(PromptCacheHandle)
            .where(
                PromptCacheHandle.cache_key == cache_key,
                PromptCacheHandle.expires_at > now,
            )
            .limit(1)
        )
        result = await self._db.execute(stmt)
        handle = result.scalar_one_or_none()
        if handle is None:
            return None

        # Refresh TTL so frequently-used handles stay alive
        handle.expires_at = now + timedelta(seconds=settings.prompt_cache_ttl_seconds)
        await self._db.flush()

        return PromptCacheResult(
            gemini_cache_id=handle.gemini_cache_id,
            handle_id=handle.id,
        )

    async def maybe_create(
        self,
        *,
        cache_key: str,
        system: str,
        kb_chunks: List[dict],  # each: {"content": "...", "title": "..."}
        tier: str,
        model: str,
    ) -> Optional[PromptCacheResult]:
        """Create a Gemini explicit cache when the hit threshold is reached.

        Returns None on first N-1 requests (below threshold) and on Gemini
        API errors (graceful degradation — LLM still works without cache).
        """
        count = _HitCounter.increment(cache_key)
        threshold = settings.prompt_cache_hit_threshold
        if count < threshold:
            return None

        # Reached threshold — call Gemini cache API
        try:
            from app.db.models.chat.prompt_cache_handle import PromptCacheHandle
        except ImportError:
            logger.debug("PromptCacheHandle model not yet available; skipping cache creation")
            return None

        try:
            handle = await asyncio.to_thread(
                self._create_gemini_cache,
                system=system,
                kb_chunks=kb_chunks,
                model=model,
            )
        except Exception:  # noqa: BLE001
            logger.exception(
                "Gemini cache creation failed for key=%s; degrading gracefully", cache_key
            )
            return None

        now = datetime.now(timezone.utc)
        row = PromptCacheHandle(
            cache_key=cache_key,
            gemini_cache_id=handle["gemini_cache_id"],
            model=model,
            token_count=handle["token_count"],
            expires_at=now + timedelta(seconds=settings.prompt_cache_ttl_seconds),
        )
        self._db.add(row)
        try:
            await self._db.flush()
            await self._db.refresh(row)
        except Exception:  # noqa: BLE001
            # Duplicate key race — another request created the handle concurrently
            logger.debug("prompt_cache insert race for key=%s; ignoring", cache_key)
            await self._db.rollback()
            return None

        _HitCounter.reset(cache_key)
        logger.info(
            "prompt_cache created handle id=%d gemini_id=%s tokens=%d model=%s",
            row.id,
            row.gemini_cache_id,
            row.token_count,
            model,
        )
        return PromptCacheResult(gemini_cache_id=row.gemini_cache_id, handle_id=row.id)

    async def invalidate_for_chunks(self, chunk_ids: List[int]) -> int:
        """Delete ALL handles (broad-strokes) when KB chunks change.

        See module docstring for trade-off rationale.
        chunk_ids kept for API symmetry; unused in DELETE.
        """
        if not chunk_ids:
            return 0
        try:
            from app.db.models.chat.prompt_cache_handle import PromptCacheHandle
        except ImportError:
            return 0

        stmt = delete(PromptCacheHandle)
        result = await self._db.execute(stmt)
        deleted = result.rowcount or 0
        logger.info(
            "prompt_cache invalidated %d handles (broad-strokes, %d chunks changed)",
            deleted,
            len(chunk_ids),
        )
        return deleted

    async def cleanup_expired(self) -> int:
        """Delete expired handles — target for nightly job."""
        try:
            from app.db.models.chat.prompt_cache_handle import PromptCacheHandle
        except ImportError:
            return 0

        now = datetime.now(timezone.utc)
        stmt = delete(PromptCacheHandle).where(PromptCacheHandle.expires_at < now)
        result = await self._db.execute(stmt)
        deleted = result.rowcount or 0
        if deleted:
            logger.info("prompt_cache cleanup: deleted %d expired handles", deleted)
        return deleted

    # ------------------------------------------------------------------
    # Private — Gemini cache API call (runs in to_thread)
    # ------------------------------------------------------------------

    def _create_gemini_cache(
        self,
        *,
        system: str,
        kb_chunks: List[dict],
        model: str,
    ) -> dict:
        """Synchronous; called via asyncio.to_thread.

        Returns dict with gemini_cache_id and token_count.
        Caller (LlmService Step 2) passes the returned gemini_cache_id as
        cached_content=<id> in GenerateContentConfig.
        """
        from google.genai import types as genai_types

        client = self._client_provider()

        # Format chunks the same way LlmService builds retrieval prompts
        chunks_text = "\n\n".join(
            f"[{c.get('title', 'chunk')}]\n{c.get('content', '')}"
            for c in kb_chunks
        )
        cache_content = f"{system}\n\n---KB CONTEXT---\n{chunks_text}"

        # google-genai caches.create — explicit cached content
        # Signature: client.caches.create(model=..., config=CachedContentConfig(...))
        # Returns CachedContent with .name (= cache id), .usage_metadata.total_token_count
        result = client.caches.create(
            model=model,
            config=genai_types.CreateCachedContentConfig(
                contents=[cache_content],
                system_instruction=system,
                ttl=f"{settings.prompt_cache_ttl_seconds}s",
            ),
        )

        gemini_cache_id = getattr(result, "name", None) or str(result)
        usage = getattr(result, "usage_metadata", None)
        token_count = int(getattr(usage, "total_token_count", 0) or 0)

        return {"gemini_cache_id": gemini_cache_id, "token_count": token_count}


__all__ = [
    "PromptCacheResult",
    "PromptCacheService",
    "invalidate_for_chunks_sync",
]
