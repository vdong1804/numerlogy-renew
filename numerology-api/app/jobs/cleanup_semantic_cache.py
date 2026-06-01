# ruff: noqa: UP045, UP017
"""Nightly cleanup job: prune expired semantic_cache rows.

Wire-up: registered in scheduler.py at 03:15 daily (offset from other 03:00 jobs).
Manual trigger: python -m app.jobs.cleanup_semantic_cache
"""

from __future__ import annotations

import asyncio
import logging

from app.db.session import async_session_factory
from app.services.chat.embedding_service import EmbeddingService
from app.services.chat.semantic_cache_service import SemanticCacheService

logger = logging.getLogger(__name__)


async def run() -> dict:
    """Delete expired rows from semantic_cache. Returns deleted row counts."""
    async with async_session_factory() as db:
        embedding_svc = EmbeddingService()
        sem_svc = SemanticCacheService(db, embedding_svc)
        sem_deleted = await sem_svc.cleanup_expired()
        await db.commit()

    logger.info("cleanup_semantic_cache: semantic_cache=%d deleted", sem_deleted)
    return {"semantic_cache": sem_deleted}


if __name__ == "__main__":
    asyncio.run(run())
