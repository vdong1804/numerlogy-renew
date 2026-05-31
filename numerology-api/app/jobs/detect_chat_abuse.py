# ruff: noqa: UP045, UP017
"""Cron: scan recent chat activity for abuse patterns + write flags (Phase 08).

Schedule: every 15 minutes via app.jobs.scheduler.
Manual: python -m app.jobs.detect_chat_abuse

Window: last 60 minutes for in-band detectors, last 30 days for quota grief
(soft signal). Detectors are idempotent — same window scan inserts equivalent
flags; admin can review/dedupe by `pattern + created_at`.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.db.session import async_session_factory
from app.services.chat.abuse_detection_service import AbuseDetectionService

logger = logging.getLogger(__name__)

# Tunables — keep as module constants so tests can monkeypatch.
WINDOW_MINUTES = 60
GRIEF_WINDOW_DAYS = 30


async def run() -> dict:
    now = datetime.now(timezone.utc)
    short_cut = now - timedelta(minutes=WINDOW_MINUTES)
    grief_cut = now - timedelta(days=GRIEF_WINDOW_DAYS)

    async with async_session_factory() as db:
        svc = AbuseDetectionService(db)
        flags: list = []
        flags += await svc.detect_rapid_quota_cycle(short_cut)
        flags += await svc.detect_identical_burst(short_cut)
        flags += await svc.detect_pdf_upload_spam(short_cut)
        flags += await svc.detect_quota_grief(grief_cut)
        written = await svc.write_flags(flags)
        await db.commit()

    counts: dict[str, int] = {}
    for f in flags:
        counts[f.pattern] = counts.get(f.pattern, 0) + 1
    logger.info("detect_chat_abuse: wrote=%d patterns=%s", written, counts)
    return {"written": written, "patterns": counts}


if __name__ == "__main__":
    asyncio.run(run())
