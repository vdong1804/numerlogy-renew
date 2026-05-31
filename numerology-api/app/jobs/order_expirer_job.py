"""Cron: expire pending orders past their deadline."""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order
from app.db.models.user import User
from app.db.session import async_session_factory
from app.services import email_outbox_service

logger = logging.getLogger(__name__)


async def run() -> dict:
    async with async_session_factory() as db:
        stats = await _run_with_db(db)
        await db.commit()
        return stats


async def _run_with_db(db: AsyncSession) -> dict:
    """Expire pending orders past ``expires_at`` and enqueue notification emails."""
    now = datetime.now(timezone.utc)
    pending_q = await db.execute(
        select(Order, User)
        .join(User, User.id == Order.user_id, isouter=True)
        .where(Order.status == "pending", Order.expires_at < now)
    )
    rows = pending_q.all()

    expired = 0
    for order, user in rows:
        order.status = "expired"
        expired += 1
        if user is not None:
            try:
                await email_outbox_service.enqueue(
                    db,
                    to_email=user.email,
                    template="order-expired",
                    payload={"ref_code": order.ref_code, "order_id": order.id},
                    user_id=user.id,
                )
            except Exception:  # noqa: BLE001
                logger.exception("expire_pending_orders: email enqueue failed")
    await db.flush()
    logger.info("expire_pending_orders: %s orders expired", expired)
    return {"expired": expired}
