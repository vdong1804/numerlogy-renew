# ruff: noqa: UP045, UP017
"""CostMonitorService — LLM cost calculation + threshold alerts (Phase 08).

Hot path callers: `chat_turn.persist_assistant_message` increments today's
metrics atomically. The full daily roll-up is owned by
`aggregate_chat_metrics` job; this service only writes incremental deltas
and reads aggregated state for alerting.

Pricing table is the single source of truth for $/token; bump on each
provider price change and ship together with `chatbot-cost-monitoring.md`
update.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.email_service import send_email

logger = logging.getLogger(__name__)

# Pricing, USD per 1 token. Update on each provider price change.
# DeepSeek-V3 (chat) is the active model; Gemini entries kept so legacy
# chat_messages rows still aggregate against their historical price.
# `cached_input` on DeepSeek reflects the auto-cache-hit price tier.
PRICING: dict[str, dict[str, float]] = {
    "deepseek-chat": {
        "input": 0.27 / 1e6,
        "output": 1.10 / 1e6,
        "cached_input": 0.07 / 1e6,
    },
    "gemini-2.0-flash": {
        "input": 0.10 / 1e6,
        "output": 0.40 / 1e6,
        "cached_input": 0.025 / 1e6,
    },
    "gemini-2.5-pro": {
        "input": 1.25 / 1e6,
        "output": 5.00 / 1e6,
        "cached_input": 0.31 / 1e6,
    },
    "text-embedding-004": {"input": 0.025 / 1e6, "output": 0},
}


def calc_msg_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cached_tokens: int = 0,
) -> Decimal:
    """Return USD cost for one message. Unknown model → 0 (logged)."""
    p = PRICING.get(model)
    if p is None:
        logger.warning("calc_msg_cost: unknown model %s", model)
        return Decimal("0")
    raw = (
        max(0, input_tokens - cached_tokens) * p["input"]
        + cached_tokens * p.get("cached_input", p["input"])
        + output_tokens * p["output"]
    )
    return Decimal(str(round(raw, 6)))


class CostMonitorService:
    """Read/write helpers around chat_daily_metrics."""

    # Default daily ceiling — $20 implies ~$600/mo at constant rate.
    DEFAULT_THRESHOLD_USD = Decimal("20")

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def record_message_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0,
        tier: str = "free",
        from_cache: bool = False,
    ) -> Decimal:
        """Increment today's row with a single message's deltas. Returns the
        computed cost USD. Caller owns commit."""
        cost = calc_msg_cost(model, input_tokens, output_tokens, cached_tokens)
        today = datetime.now(timezone.utc).date()
        # Free vs paid bucket — `addon` / `pro` count as paid; everything else free.
        is_paid = tier in ("pro", "paid")
        # Postgres UPSERT — SQLite emulates via ON CONFLICT (same syntax).
        await self.db.execute(
            text(
                """
                INSERT INTO chat_daily_metrics (
                    date, msg_count_free, msg_count_paid, cache_hits,
                    input_tokens_total, output_tokens_total, cost_usd
                ) VALUES (
                    :d, :free_inc, :paid_inc, :cache_inc,
                    :in_t, :out_t, :cost
                )
                ON CONFLICT (date) DO UPDATE SET
                    msg_count_free = chat_daily_metrics.msg_count_free + :free_inc,
                    msg_count_paid = chat_daily_metrics.msg_count_paid + :paid_inc,
                    cache_hits = chat_daily_metrics.cache_hits + :cache_inc,
                    input_tokens_total = chat_daily_metrics.input_tokens_total + :in_t,
                    output_tokens_total = chat_daily_metrics.output_tokens_total + :out_t,
                    cost_usd = chat_daily_metrics.cost_usd + :cost
                """
            ),
            {
                "d": today,
                "free_inc": 0 if is_paid else 1,
                "paid_inc": 1 if is_paid else 0,
                "cache_inc": 1 if from_cache else 0,
                "in_t": input_tokens,
                "out_t": output_tokens,
                # aiosqlite can't bind Decimal directly; str round-trips fine on PG NUMERIC.
                "cost": str(cost),
            },
        )
        return cost

    async def increment_rate_limit_hit(self) -> None:
        """Bump today's rate_limit_hits counter. Caller owns commit."""
        today = datetime.now(timezone.utc).date()
        await self.db.execute(
            text(
                """
                INSERT INTO chat_daily_metrics (date, rate_limit_hits)
                VALUES (:d, 1)
                ON CONFLICT (date) DO UPDATE
                SET rate_limit_hits = chat_daily_metrics.rate_limit_hits + 1
                """
            ),
            {"d": today},
        )

    async def get_today_cost(self) -> Decimal:
        today = datetime.now(timezone.utc).date()
        row = (
            await self.db.execute(
                text("SELECT cost_usd FROM chat_daily_metrics WHERE date = :d"),
                {"d": today},
            )
        ).first()
        return Decimal(str(row[0])) if row else Decimal("0")

    async def get_cost_for_date(self, d: date) -> Decimal:
        row = (
            await self.db.execute(
                text("SELECT cost_usd FROM chat_daily_metrics WHERE date = :d"),
                {"d": d},
            )
        ).first()
        return Decimal(str(row[0])) if row else Decimal("0")

    async def alert_if_exceeded(
        self,
        threshold_usd: Optional[Decimal] = None,
        slack_webhook: Optional[str] = None,
        admin_email: Optional[str] = None,
    ) -> bool:
        """Send email + Slack alert when today's cost > threshold.

        Returns True if alert was fired. Safe to call repeatedly — the caller
        should rate-limit (e.g. 1×/hour via the aggregate job)."""
        threshold = threshold_usd or self.DEFAULT_THRESHOLD_USD
        cost = await self.get_today_cost()
        if cost <= threshold:
            return False
        msg = (
            f"[Numerology Chat] Daily cost alert: ${cost} exceeds threshold ${threshold}. "
            f"Date: {datetime.now(timezone.utc).date()}."
        )
        logger.warning(msg)
        if admin_email:
            try:
                # send_email is sync (smtplib); fine inside an async fn — single small call.
                send_email(
                    to_email=admin_email,
                    subject="Chatbot daily cost alert",
                    body=msg,
                )
            except Exception:  # noqa: BLE001
                logger.exception("cost alert: email send failed")
        if slack_webhook:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(slack_webhook, json={"text": msg})
            except Exception:  # noqa: BLE001
                logger.exception("cost alert: Slack webhook failed")
        return True


__all__ = ["CostMonitorService", "PRICING", "calc_msg_cost"]
