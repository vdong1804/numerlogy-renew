"""ChatDailyMetrics — one row per UTC date with aggregated cost/usage rollup (Phase 08).

Written by `aggregate_chat_metrics` job:
- hourly tick → incremental upsert for today
- nightly tick (03:30 UTC) → finalize previous day + recompute unique_users

Read by:
- cost_monitor_service.alert_if_exceeded()
- admin cost dashboard
"""

from datetime import date as date_type, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ChatDailyMetrics(Base):
    __tablename__ = "chat_daily_metrics"

    date: Mapped[date_type] = mapped_column(Date, primary_key=True)
    msg_count_free: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    msg_count_paid: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    cache_hits: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    input_tokens_total: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )
    output_tokens_total: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )
    cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), nullable=False, default=Decimal("0"), server_default="0"
    )
    rate_limit_hits: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    new_addon_purchases: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    unique_users: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )


__all__ = ["ChatDailyMetrics"]
