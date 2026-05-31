# ruff: noqa: UP045, UP017
"""RateLimitBucket — token-bucket state row per (user / IP) key.

bucket_key is the primary key (e.g. 'user:42' or 'ip:1.2.3.4').
All mutations use SELECT FOR UPDATE to serialise concurrent requests
without needing Redis. Move to Redis if sustained RPS exceeds ~100.
"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RateLimitBucket(Base):
    __tablename__ = "rate_limit_buckets"

    # Natural PK — 'user:<id>' or 'ip:<addr>'
    bucket_key: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Token-bucket math fields
    tokens: Mapped[object] = mapped_column(Numeric(10, 2), nullable=False)
    capacity: Mapped[object] = mapped_column(Numeric(10, 2), nullable=False)
    # tokens added per second
    refill_rate: Mapped[object] = mapped_column(Numeric(10, 4), nullable=False)

    last_refill: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
    )

    # Daily rolling counter — reset when daily_reset_date < CURRENT_DATE
    daily_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    daily_reset_date: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=func.current_date()
    )


__all__ = ["RateLimitBucket"]
