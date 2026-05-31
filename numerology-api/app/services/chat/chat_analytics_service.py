# ruff: noqa: UP045, UP017
"""Read-only SQL aggregations for the admin analytics dashboard (Phase 07).

All queries operate on existing chat_* tables; no extra writes. We keep the
service pure SQL (no LLM calls) so a 30-day window typically returns in <1s
against PG with the indexes already present from Phase 01-06.

Pricing constants are best-effort — used only for the "estimated cost" card
in the admin UI; they're not billing-grade.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat.chat_addon_purchase import ChatAddonPurchase
from app.db.models.chat.conversation import ChatConversation
from app.db.models.chat.message import ChatMessage
from app.db.models.chat.prompt_cache_handle import PromptCacheHandle
from app.db.models.chat.semantic_cache_entry import SemanticCacheEntry

# Gemini pricing per 1M tokens (USD) — Jan 2026, rough.
# Keys match `chat_messages.model_used`; default fallback used for unknown models.
GEMINI_PRICING: dict[str, tuple[float, float]] = {
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-2.0-pro": (1.25, 5.00),
    "gemini-2.5-pro": (1.25, 5.00),
}
_DEFAULT_PRICE = (0.20, 0.80)


@dataclass
class DailyMessageStat:
    day: str  # YYYY-MM-DD
    tier: str
    count: int


@dataclass
class TopQuestion:
    question: str
    count: int


@dataclass
class CostByModel:
    model: str
    input_tokens: int
    output_tokens: int
    estimated_usd: float


@dataclass
class AnalyticsOverview:
    window_start: str
    window_end: str
    total_messages: int
    total_conversations: int
    unique_users: int
    messages_by_day: list[DailyMessageStat]
    top_questions: list[TopQuestion]
    cost_by_model: list[CostByModel]
    estimated_total_cost_usd: float
    semantic_cache_entries: int
    semantic_cache_hits: int
    semantic_cache_hit_rate: float
    prompt_cache_active_handles: int
    addon_purchases: int

    def to_dict(self) -> dict:
        return asdict(self)


class ChatAnalyticsService:
    """SQL aggregations for the admin dashboard."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def overview(
        self,
        start: date,
        end: date,
        top_question_limit: int = 10,
    ) -> AnalyticsOverview:
        start_dt = datetime.combine(start, time.min, tzinfo=timezone.utc)
        end_dt = datetime.combine(end + timedelta(days=1), time.min, tzinfo=timezone.utc)

        total_messages = await self._scalar(
            select(func.count(ChatMessage.id)).where(
                ChatMessage.created_at >= start_dt,
                ChatMessage.created_at < end_dt,
            )
        )
        total_conversations = await self._scalar(
            select(func.count(ChatConversation.id)).where(
                ChatConversation.created_at >= start_dt,
                ChatConversation.created_at < end_dt,
            )
        )
        unique_users = await self._scalar(
            select(func.count(func.distinct(ChatConversation.user_id))).where(
                ChatConversation.created_at >= start_dt,
                ChatConversation.created_at < end_dt,
            )
        )

        messages_by_day = await self._daily_breakdown(start_dt, end_dt)
        top_questions = await self._top_questions(start_dt, end_dt, top_question_limit)
        cost_breakdown = await self._cost_breakdown(start_dt, end_dt)
        estimated_total = sum(c.estimated_usd for c in cost_breakdown)

        semantic_entries, semantic_hits = await self._semantic_cache_stats(start_dt, end_dt)
        # Hit rate denominator = assistant answers actually generated + cache
        # hits. Including user rows under-states the rate; including all rows
        # over-states it. (cache_hit OR llm_answer) is the answered query count.
        assistant_count = await self._scalar(
            select(func.count(ChatMessage.id)).where(
                ChatMessage.created_at >= start_dt,
                ChatMessage.created_at < end_dt,
                ChatMessage.role == "assistant",
            )
        )
        hit_rate = (
            semantic_hits / (semantic_hits + assistant_count)
            if (semantic_hits + assistant_count) > 0
            else 0.0
        )
        prompt_cache_active = await self._scalar(
            select(func.count(PromptCacheHandle.id)).where(
                PromptCacheHandle.expires_at > datetime.now(timezone.utc)
            )
        )
        addon_purchases = await self._scalar(
            select(func.count(ChatAddonPurchase.id)).where(
                ChatAddonPurchase.purchased_at >= start_dt,
                ChatAddonPurchase.purchased_at < end_dt,
            )
        )

        return AnalyticsOverview(
            window_start=start.isoformat(),
            window_end=end.isoformat(),
            total_messages=total_messages,
            total_conversations=total_conversations,
            unique_users=unique_users,
            messages_by_day=messages_by_day,
            top_questions=top_questions,
            cost_by_model=cost_breakdown,
            estimated_total_cost_usd=round(estimated_total, 4),
            semantic_cache_entries=semantic_entries,
            semantic_cache_hits=semantic_hits,
            semantic_cache_hit_rate=round(hit_rate, 4),
            prompt_cache_active_handles=prompt_cache_active,
            addon_purchases=addon_purchases,
        )

    # -- Internal helpers ----------------------------------------------------

    async def _scalar(self, stmt) -> int:
        result = await self._db.execute(stmt)
        return int(result.scalar() or 0)

    async def _daily_breakdown(self, start_dt: datetime, end_dt: datetime) -> list[DailyMessageStat]:
        day_col = func.date(ChatMessage.created_at).label("day")
        tier_col = func.coalesce(ChatMessage.tier, "unknown").label("tier")
        stmt = (
            select(day_col, tier_col, func.count(ChatMessage.id))
            .where(
                ChatMessage.created_at >= start_dt,
                ChatMessage.created_at < end_dt,
            )
            .group_by(day_col, tier_col)
            .order_by(day_col, tier_col)
        )
        rows = (await self._db.execute(stmt)).all()
        return [
            DailyMessageStat(day=str(d), tier=str(t), count=int(c))
            for (d, t, c) in rows
        ]

    async def _top_questions(
        self, start_dt: datetime, end_dt: datetime, limit: int
    ) -> list[TopQuestion]:
        stmt = (
            select(ChatMessage.content, func.count(ChatMessage.id).label("c"))
            .where(
                ChatMessage.created_at >= start_dt,
                ChatMessage.created_at < end_dt,
                ChatMessage.role == "user",
            )
            .group_by(ChatMessage.content)
            .order_by(func.count(ChatMessage.id).desc())
            .limit(limit)
        )
        rows = (await self._db.execute(stmt)).all()
        return [TopQuestion(question=str(q), count=int(c)) for (q, c) in rows]

    async def _cost_breakdown(self, start_dt: datetime, end_dt: datetime) -> list[CostByModel]:
        model_col = func.coalesce(ChatMessage.model_used, "unknown").label("m")
        # Only assistant rows have non-zero token counts in practice; filter to
        # avoid double-counting if user rows accidentally got tokens stamped.
        stmt = (
            select(
                model_col,
                func.sum(case((ChatMessage.role == "assistant", ChatMessage.input_tokens), else_=0)),
                func.sum(case((ChatMessage.role == "assistant", ChatMessage.output_tokens), else_=0)),
            )
            .where(
                ChatMessage.created_at >= start_dt,
                ChatMessage.created_at < end_dt,
            )
            .group_by(model_col)
        )
        rows = (await self._db.execute(stmt)).all()
        out: list[CostByModel] = []
        for model, in_toks, out_toks in rows:
            in_n = int(in_toks or 0)
            out_n = int(out_toks or 0)
            in_price, out_price = GEMINI_PRICING.get(str(model), _DEFAULT_PRICE)
            cost = (in_n / 1_000_000) * in_price + (out_n / 1_000_000) * out_price
            out.append(
                CostByModel(
                    model=str(model),
                    input_tokens=in_n,
                    output_tokens=out_n,
                    estimated_usd=round(cost, 4),
                )
            )
        out.sort(key=lambda x: x.estimated_usd, reverse=True)
        return out

    async def _semantic_cache_stats(
        self, start_dt: datetime, end_dt: datetime
    ) -> tuple[int, int]:
        stmt = select(
            func.count(SemanticCacheEntry.id),
            func.coalesce(func.sum(SemanticCacheEntry.hit_count), 0),
        ).where(
            SemanticCacheEntry.created_at >= start_dt,
            SemanticCacheEntry.created_at < end_dt,
        )
        row = (await self._db.execute(stmt)).one_or_none()
        if not row:
            return 0, 0
        entries, hits = row
        return int(entries or 0), int(hits or 0)


def default_window(days: int = 30) -> tuple[date, date]:
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days - 1)
    return start, end


__all__ = [
    "ChatAnalyticsService",
    "AnalyticsOverview",
    "DailyMessageStat",
    "TopQuestion",
    "CostByModel",
    "GEMINI_PRICING",
    "default_window",
]
