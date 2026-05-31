"""Cron: delete expired user_pdf_index rows + stale temp upload files.

Runs nightly at 03:00. UserPdfChunk rows cascade automatically via FK ON DELETE
CASCADE. We also sweep temp files older than 1h from media/chat_uploads/.
"""

import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import delete

from app.config import settings
from app.db.models.chat.user_pdf_index import UserPdfIndex
from app.db.session import async_session_factory

logger = logging.getLogger(__name__)

# Temp uploads (per-user dir) — anything older than this is removed.
TEMP_FILE_TTL_SECONDS = 60 * 60  # 1 hour
TEMP_UPLOAD_SUBDIR = "chat_uploads"


async def run() -> dict:
    deleted_rows = await _delete_expired_indexes()
    removed_files = _sweep_temp_uploads()
    logger.info(
        "cleanup_user_pdfs: %d expired indexes deleted, %d temp files removed",
        deleted_rows, removed_files,
    )
    return {"deleted_indexes": deleted_rows, "removed_files": removed_files}


async def _delete_expired_indexes() -> int:
    now = datetime.now(timezone.utc)
    async with async_session_factory() as db:
        result = await db.execute(
            delete(UserPdfIndex).where(UserPdfIndex.expires_at < now)
        )
        await db.commit()
        return int(result.rowcount or 0)


def _sweep_temp_uploads() -> int:
    base = Path(settings.media_root) / TEMP_UPLOAD_SUBDIR
    if not base.exists():
        return 0
    cutoff = time.time() - TEMP_FILE_TTL_SECONDS
    removed = 0
    for p in base.rglob("*"):
        if not p.is_file():
            continue
        try:
            if p.stat().st_mtime < cutoff:
                p.unlink()
                removed += 1
        except OSError:
            logger.warning("cleanup_user_pdfs: cannot remove %s", p, exc_info=True)
    return removed
