"""Reconcile-SePay cron job — runs every 15 minutes via APScheduler.

Algorithm:
1. Query orders WHERE status='pending' AND created_at >= now() - RECONCILE_WINDOW_HOURS
2. Fetch SePay recent transactions (same window)
3. For each tx with a parseable ref_code matching a pending order:
   a. Check webhook_events for existing row (idempotency — any provider)
   b. If no row: mark order paid, call fulfillment_service.fulfill_order,
      insert webhook_events row with provider='reconcile'
4. Log matched / fulfilled / errors counts

Manual trigger: python -m app.jobs.reconcile_sepay
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.db.models.order import Order
from app.db.models.webhook_event import WebhookEvent
from app.db.session import async_session_factory

logger = logging.getLogger(__name__)


async def run() -> dict:
    """Execute one reconcile pass. Returns counters dict."""
    from app.services import fulfillment_service
    from app.services.sepay_service import list_recent_transactions

    window_hours = settings.reconcile_window_hours
    since = datetime.now(timezone.utc) - timedelta(hours=window_hours)

    counters = {"checked": 0, "matched": 0, "fulfilled": 0, "errors": 0, "skipped_idempotent": 0}

    # Fetch SePay transactions first — if API fails, abort early
    transactions = await list_recent_transactions(hours=window_hours)
    if not transactions:
        logger.info("reconcile_sepay: no transactions returned from SePay API")
        return counters

    # Build ref_code → tx lookup (only entries with a ref_code)
    tx_by_ref: dict[str, dict] = {}
    for tx in transactions:
        if tx["ref_code"]:
            tx_by_ref[tx["ref_code"]] = tx

    if not tx_by_ref:
        logger.info("reconcile_sepay: no parseable ref_codes in %d transactions", len(transactions))
        return counters

    async with async_session_factory() as db:
        # Load pending orders in window
        result = await db.execute(
            select(Order).where(
                Order.status == "pending",
                Order.created_at >= since,
            )
        )
        pending_orders = result.scalars().all()
        counters["checked"] = len(pending_orders)

        for order in pending_orders:
            tx = tx_by_ref.get(order.ref_code)
            if tx is None:
                continue

            counters["matched"] += 1

            # Idempotency: check webhook_events for ANY successful event for this order
            # across both 'sepay' and 'reconcile' providers to avoid double-fulfillment.
            existing = await db.execute(
                select(WebhookEvent).where(
                    WebhookEvent.order_id == order.id,
                    WebhookEvent.provider.in_(["sepay", "reconcile"]),
                    WebhookEvent.status.in_(["matched", "received", "duplicate"]),
                )
            )
            if existing.scalar_one_or_none() is not None:
                counters["skipped_idempotent"] += 1
                continue

            # Re-lock the row to prevent race with live webhook
            locked = await db.execute(
                select(Order).where(Order.id == order.id).with_for_update()
            )
            locked_order = locked.scalar_one()
            if locked_order.status != "pending":
                counters["skipped_idempotent"] += 1
                continue

            try:
                # Mark order paid
                locked_order.status = "paid"
                locked_order.paid_at = datetime.now(timezone.utc)
                locked_order.sepay_tx_id = tx["id"]

                await fulfillment_service.fulfill_order(db, locked_order)

                # Insert reconcile audit row
                event = WebhookEvent(
                    provider="reconcile",
                    sepay_tx_id=tx["id"],
                    status="matched",
                    order_id=locked_order.id,
                    ref_code=order.ref_code,
                    amount=tx["amount"],
                    raw_payload={"source": "reconcile_cron", "tx_id": tx["id"]},
                )
                db.add(event)
                await db.flush()

                # Commit per-order so a later failure does not roll back
                # already-fulfilled orders.
                await db.commit()

                counters["fulfilled"] += 1
                logger.info(
                    "reconcile_sepay: fulfilled order %s ref=%s amount=%s",
                    locked_order.id, order.ref_code, tx["amount"],
                )
            except IntegrityError:
                await db.rollback()
                counters["skipped_idempotent"] += 1
                logger.info("reconcile_sepay: IntegrityError for order %s — already processed", order.id)
            except Exception as exc:  # noqa: BLE001
                await db.rollback()
                counters["errors"] += 1
                logger.exception("reconcile_sepay: fulfillment failed for order %s: %s", order.id, exc)

    logger.info(
        "reconcile_sepay done: checked=%d matched=%d fulfilled=%d skipped=%d errors=%d",
        counters["checked"], counters["matched"], counters["fulfilled"],
        counters["skipped_idempotent"], counters["errors"],
    )
    return counters


# Allow manual trigger: python -m app.jobs.reconcile_sepay
if __name__ == "__main__":
    asyncio.run(run())
