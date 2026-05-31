# ruff: noqa: UP045, UP017, UP041
"""SQLAlchemy event listeners that re-embed numerology content on CRUD.

Mapper-level `after_insert/update/delete` captures the row data into a
session-local pending list. Session-level `after_commit` drains that list
onto an asyncio queue; `after_rollback` discards it. This avoids the
phantom-doc race where a row enqueued during flush gets rolled back later.

A single asyncio worker (per-process singleton) drains the queue and calls
KbIngestionService so embeddings live off the request thread.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import async_session_factory
from app.services.chat.embedding_service import EmbeddingService
from app.services.chat.kb_ingestion_service import KbIngestionService
from app.services.chat.prompt_cache_service import invalidate_for_chunks_sync

logger = logging.getLogger(__name__)

# Module-level singletons — created on first register_kb_sync_listeners call.
_queue: Optional[asyncio.Queue] = None
_worker_task: Optional[asyncio.Task] = None
_registered_models: set[type[Base]] = set()
_session_hooks_attached = False
_EXTRA_CONTENT_FIELDS = ("content_2", "content_3", "content_4", "content_5")
_PENDING_KEY = "kb_sync_pending"  # session.info key


def _to_source(target: Any) -> tuple[str, str, Optional[str], str]:
    """Map a content row to (source_type, source_ref, title, joined_content)."""
    table = type(target).__tablename__
    parts = [getattr(target, "content", "") or ""]
    for fld in _EXTRA_CONTENT_FIELDS:
        v = getattr(target, fld, None)
        if v:
            parts.append(v)
    return (
        f"numerology:{table}",
        target.code,
        getattr(target, "title", None),
        "\n\n".join(parts),
    )


def _stash(session: Session, action: str, target: Any) -> None:
    """Capture row payload into session-local list; drained on after_commit."""
    source_type, source_ref, title, content = _to_source(target)
    session.info.setdefault(_PENDING_KEY, []).append(
        (action, source_type, source_ref, title, content)
    )


def _on_save(mapper, connection, target):  # noqa: ARG001
    state = getattr(target, "_sa_instance_state", None)
    if state and state.session is not None:
        _stash(state.session, "upsert", target)


def _on_delete(mapper, connection, target):  # noqa: ARG001
    state = getattr(target, "_sa_instance_state", None)
    if state and state.session is not None:
        _stash(state.session, "delete", target)


def _on_after_commit(session: Session) -> None:
    """Flush pending items onto the asyncio queue after the txn commits.

    Also invalidates all Gemini prompt-cache handles (broad-strokes) when KB
    chunks change.  Broad-strokes means we delete every handle regardless of
    which chunks it references, because the cache_key encodes sorted chunk ids
    but we store no reverse index.  With a 1h TTL the worst-case stale window
    is eliminated immediately.  Phase 08 adds fine-grained per-chunk lookup.
    """
    pending = session.info.pop(_PENDING_KEY, None)
    if not pending or _queue is None:
        return
    for item in pending:
        try:
            _queue.put_nowait(item)
        except asyncio.QueueFull:
            logger.warning("kb_sync queue full; dropping %s for %s/%s",
                           item[0], item[1], item[2])

    # Invalidate prompt-cache handles so stale Gemini caches are not reused
    # after KB content changes.  Runs synchronously in the after_commit hook
    # using a plain SQL DELETE (no async session needed).
    # pending tuples are (action, source_type, source_ref, title, content);
    # we pass len(pending) sentinel ids — invalidate_for_chunks_sync uses
    # broad-strokes DELETE ALL so exact ids are not required, only a non-empty
    # list to signal that something changed.
    sentinel_ids = list(range(1, len(pending) + 1))
    invalidate_for_chunks_sync(session, sentinel_ids)


def _on_after_rollback(session: Session) -> None:
    session.info.pop(_PENDING_KEY, None)


async def _process_one(item: tuple) -> None:
    action, source_type, source_ref, title, content = item
    async with async_session_factory() as session:
        svc = KbIngestionService(session, EmbeddingService())
        try:
            if action == "upsert":
                await svc.upsert_document(source_type, source_ref, title, content)
            else:
                await svc.delete_document(source_type, source_ref)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def _worker() -> None:
    assert _queue is not None
    while True:
        item = await _queue.get()
        try:
            await _process_one(item)
        except Exception:  # noqa: BLE001
            logger.exception("kb_sync worker failed for item=%s", item[:3])
        finally:
            _queue.task_done()


def register_kb_sync_listeners(models: list[type[Base]]) -> None:
    """Idempotently attach mapper + session listeners and start the worker."""
    global _queue, _worker_task, _session_hooks_attached
    if _queue is None:
        _queue = asyncio.Queue(maxsize=1000)
    if _worker_task is None or _worker_task.done():
        _worker_task = asyncio.create_task(_worker(), name="kb-sync-worker")
    if not _session_hooks_attached:
        event.listen(Session, "after_commit", _on_after_commit)
        event.listen(Session, "after_rollback", _on_after_rollback)
        _session_hooks_attached = True
    added = 0
    for model in models:
        if model in _registered_models:
            continue
        event.listen(model, "after_insert", _on_save)
        event.listen(model, "after_update", _on_save)
        event.listen(model, "after_delete", _on_delete)
        _registered_models.add(model)
        added += 1
    logger.info("kb_sync listeners: %d newly attached, %d total models",
                added, len(_registered_models))


async def shutdown_kb_sync() -> None:
    """Drain remaining queue then cancel the worker. Call from lifespan teardown."""
    global _worker_task
    if _queue is not None:
        try:
            await asyncio.wait_for(_queue.join(), timeout=10)
        except asyncio.TimeoutError:
            logger.warning("kb_sync drain timeout; cancelling with items pending")
    if _worker_task and not _worker_task.done():
        _worker_task.cancel()
        try:
            await _worker_task
        except (asyncio.CancelledError, Exception):  # noqa: BLE001
            pass
    _worker_task = None


def _reset_for_tests() -> None:  # pragma: no cover - test helper
    global _queue, _worker_task, _session_hooks_attached
    if _worker_task and not _worker_task.done():
        _worker_task.cancel()
    _queue = None
    _worker_task = None
    _registered_models.clear()
    _session_hooks_attached = False
