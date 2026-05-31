# ruff: noqa: UP045, UP017
"""Aggregate chat metrics (Phase 08).

Two tick variants:
- ``run_hourly`` — recompute today's row from ChatMessage + ChatAddonPurchase.
  Runs every hour. Idempotent: full overwrite of today's aggregates.
- ``run_nightly`` — finalize yesterday's row + fire cost alert.
  Runs once daily at 03:30 UTC (after 03:00/03:15 cleanups).

Manual trigger:
  python -m app.jobs.aggregate_chat_metrics            # hourly tick
  python -m app.jobs.aggregate_chat_metrics --nightly  # nightly finalize
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import text

from app.config import settings
from app.db.session import async_session_factory
from app.services.chat.cost_monitor_service import PRICING, CostMonitorService

logger = logging.getLogger(__name__)


async def _recompute_for_date(db, target: date) -> dict:
    """Overwrite the chat_daily_metrics row for `target` from raw tables.

    Recomputes msg_count_free / msg_count_paid / cache_hits / token totals /
    cost_usd over the [target, target+1) UTC window. Range filter (vs
    `CAST(.. AS DATE)`) keeps the query portable PG <-> SQLite.
    """
    day_start = datetime(target.year, target.month, target.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)
    rows = (
        await db.execute(
            text(
                """
                SELECT model_used, tier, input_tokens, output_tokens
                FROM chat_messages
                WHERE role = 'assistant'
                  AND created_at >= :start AND created_at < :end
                """
            ),
            {"start": day_start, "end": day_end},
        )
    ).all()

    msg_free = msg_paid = cache_hits = 0
    in_total = out_total = 0
    cost = Decimal("0")
    flash_model = settings.gemini_flash_model
    pro_model = settings.gemini_pro_model
    for model_used, tier, in_t, out_t in rows:
        if model_used == "cache":
            cache_hits += 1
        if tier in ("pro", "paid"):
            msg_paid += 1
        else:
            msg_free += 1
        in_total += int(in_t or 0)
        out_total += int(out_t or 0)
        # Skip cost calc for cache hits (no LLM call billed).
        if model_used == "cache" or not model_used:
            continue
        model_key = model_used
        if model_used.startswith("gemini-2.0-flash"):
            model_key = flash_model if flash_model in PRICING else "gemini-2.0-flash"
        elif model_used.startswith("gemini-2.5-pro") or model_used.startswith(
            "gemini-2.0-pro"
        ):
            model_key = pro_model if pro_model in PRICING else "gemini-2.5-pro"
        from app.services.chat.cost_monitor_service import calc_msg_cost  # local import
        cost += calc_msg_cost(model_key, int(in_t or 0), int(out_t or 0))

    new_addons = (
        await db.execute(
            text(
                """
                SELECT COUNT(*) FROM chat_addon_purchases
                WHERE purchased_at >= :start AND purchased_at < :end
                """
            ),
            {"start": day_start, "end": day_end},
        )
    ).scalar_one()

    unique_users = (
        await db.execute(
            text(
                """
                SELECT COUNT(DISTINCT c.user_id)
                FROM chat_messages m
                JOIN chat_conversations c ON c.id = m.conversation_id
                WHERE m.created_at >= :start AND m.created_at < :end
                """
            ),
            {"start": day_start, "end": day_end},
        )
    ).scalar_one()

    await db.execute(
        text(
            """
            INSERT INTO chat_daily_metrics (
                date, msg_count_free, msg_count_paid, cache_hits,
                input_tokens_total, output_tokens_total, cost_usd,
                new_addon_purchases, unique_users
            ) VALUES (
                :d, :mf, :mp, :ch, :int_, :outt, :cost, :na, :uu
            )
            ON CONFLICT (date) DO UPDATE SET
                msg_count_free = EXCLUDED.msg_count_free,
                msg_count_paid = EXCLUDED.msg_count_paid,
                cache_hits = EXCLUDED.cache_hits,
                input_tokens_total = EXCLUDED.input_tokens_total,
                output_tokens_total = EXCLUDED.output_tokens_total,
                cost_usd = EXCLUDED.cost_usd,
                new_addon_purchases = EXCLUDED.new_addon_purchases,
                unique_users = EXCLUDED.unique_users
            """
        ),
        {
            "d": target,
            "mf": msg_free,
            "mp": msg_paid,
            "ch": cache_hits,
            "int_": in_total,
            "outt": out_total,
            # str() so aiosqlite can bind; PG NUMERIC accepts a string literal.
            "cost": str(cost),
            "na": int(new_addons or 0),
            "uu": int(unique_users or 0),
        },
    )
    return {
        "date": target.isoformat(),
        "msg_free": msg_free,
        "msg_paid": msg_paid,
        "cache_hits": cache_hits,
        "cost_usd": str(cost),
        "new_addons": int(new_addons or 0),
        "unique_users": int(unique_users or 0),
    }


async def run_hourly() -> dict:
    today = datetime.now(timezone.utc).date()
    async with async_session_factory() as db:
        stats = await _recompute_for_date(db, today)
        # Cost alert check after recompute (cheap — single SELECT).
        cm = CostMonitorService(db)
        slack = os.getenv("CHAT_COST_ALERT_SLACK_WEBHOOK") or None
        admin_email = os.getenv("CHAT_COST_ALERT_EMAIL") or None
        await cm.alert_if_exceeded(
            slack_webhook=slack, admin_email=admin_email
        )
        await db.commit()
    logger.info("aggregate_chat_metrics.hourly: %s", stats)
    return stats


async def run_nightly() -> dict:
    yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
    async with async_session_factory() as db:
        stats = await _recompute_for_date(db, yesterday)
        await db.commit()
    logger.info("aggregate_chat_metrics.nightly: finalized %s", stats)
    return stats


# Alias for scheduler registration parity with other jobs (`.run`).
run = run_hourly


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--nightly", action="store_true")
    args = parser.parse_args()
    asyncio.run(run_nightly() if args.nightly else run_hourly())
