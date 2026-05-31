"""APScheduler in-process configuration.

Registered at FastAPI startup. Jobs are idempotent by design — missing a tick
on restart is acceptable.
"""

import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.jobs import (
    aggregate_chat_metrics,
    cleanup_semantic_cache,
    cleanup_user_pdfs,
    detect_chat_abuse,
    email_dispatcher_job,
    order_expirer_job,
    outbox_cleanup_job,
    reconcile_sepay,
)

logger = logging.getLogger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone="Asia/Bangkok")
    return _scheduler


def setup_jobs() -> AsyncIOScheduler:
    sch = get_scheduler()
    if sch.running:
        return sch

    sch.add_job(email_dispatcher_job.run_once, "interval", minutes=1, id="email_dispatcher", replace_existing=True)
    sch.add_job(order_expirer_job.run, "interval", minutes=5, id="expire_orders", replace_existing=True)
    sch.add_job(outbox_cleanup_job.run, "cron", hour=3, minute=0, id="cleanup_outbox", replace_existing=True)
    sch.add_job(reconcile_sepay.run, "interval", minutes=15, id="reconcile_sepay", replace_existing=True)
    sch.add_job(cleanup_user_pdfs.run, "cron", hour=3, minute=0, id="cleanup_user_pdfs", replace_existing=True)
    sch.add_job(cleanup_semantic_cache.run, "cron", hour=3, minute=15, id="cleanup_semantic_cache", replace_existing=True)
    # Phase 08: chat hardening jobs.
    sch.add_job(
        aggregate_chat_metrics.run_hourly, "cron", minute=0,
        id="aggregate_chat_metrics_hourly", replace_existing=True,
    )
    sch.add_job(
        aggregate_chat_metrics.run_nightly, "cron", hour=3, minute=30,
        id="aggregate_chat_metrics_nightly", replace_existing=True,
    )
    sch.add_job(
        detect_chat_abuse.run, "interval", minutes=15,
        id="detect_chat_abuse", replace_existing=True,
    )
    logger.info("Scheduler jobs registered: %s", [j.id for j in sch.get_jobs()])
    return sch


def start() -> None:
    sch = setup_jobs()
    if not sch.running:
        sch.start()
        logger.info("Scheduler started")


def shutdown() -> None:
    sch = get_scheduler()
    if sch.running:
        sch.shutdown(wait=False)
        logger.info("Scheduler stopped")
