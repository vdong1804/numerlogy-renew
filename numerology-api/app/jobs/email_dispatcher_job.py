"""Standalone email dispatcher entry point.

Usage:
    python -m app.jobs.email_dispatcher_job [--loop]

Without --loop runs one batch then exits. With --loop sleeps 60s and runs again.
Designed to be scheduled by cron (one-shot) or by docker-compose (loop mode).
"""

import argparse
import asyncio
import logging

from app.db.session import async_session_factory
from app.services import email_outbox_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


async def run_once() -> dict:
    async with async_session_factory() as db:
        stats = await email_outbox_service.dispatch_batch(db, limit=50)
        await db.commit()
        return stats


async def run_loop(interval: int = 60) -> None:
    while True:
        try:
            stats = await run_once()
            logger.info("email dispatcher tick: %s", stats)
        except Exception:  # noqa: BLE001
            logger.exception("dispatcher iteration failed")
        await asyncio.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true", help="Keep running, sleeping 60s")
    parser.add_argument("--interval", type=int, default=60)
    args = parser.parse_args()
    if args.loop:
        asyncio.run(run_loop(args.interval))
    else:
        stats = asyncio.run(run_once())
        print(stats)


if __name__ == "__main__":
    main()
