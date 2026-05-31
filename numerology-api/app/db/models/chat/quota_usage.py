"""ChatQuotaUsage — per-user, per-day counter of free vs paid chatbot turns.

Composite PK (user_id, date) → single row per user-day, upserted on each turn.
Free / paid tiers split allows future business rules (e.g. premium top-up).
"""

from datetime import date as date_type

from sqlalchemy import BigInteger, Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ChatQuotaUsage(Base):
    __tablename__ = "chat_quota_usage"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    date: Mapped[date_type] = mapped_column(Date, primary_key=True)
    free_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    paid_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")


__all__ = ["ChatQuotaUsage"]
