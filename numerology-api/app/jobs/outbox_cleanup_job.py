"""Cron: trim old `email_outbox` rows (status=sent and older than 30 days)."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from app.db.models.email_outbox import EmailOutbox
from app.db.session import async_session_factory

logger = logging.getLogger(__name__)


async def run() -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    async with async_session_factory() as db:
        result = await db.execute(
            delete(EmailOutbox)
            .where(EmailOutbox.status == "sent", EmailOutbox.sent_at < cutoff)
        )
        await db.commit()
    deleted = result.rowcount or 0
    logger.info("cleanup_outbox: deleted %s rows", deleted)
    return {"deleted": deleted}
