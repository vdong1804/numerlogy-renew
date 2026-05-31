"""WebhookEvent — provider webhook audit log + idempotency key store."""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="sepay")
    sepay_tx_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # 'received' | 'matched' | 'unmatched' | 'duplicate' | 'amount_mismatch' | 'error'
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="received", index=True)
    order_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    ref_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("provider", "sepay_tx_id", name="uq_webhook_events_provider_tx"),
    )


__all__ = ["WebhookEvent"]
