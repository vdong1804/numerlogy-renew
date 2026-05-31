# ruff: noqa: UP045  — Optional[X] required; str|None breaks SQLAlchemy on Python 3.9
"""ChatAddonPurchase — per-user purchased message quota from a chat add-on package.

One row per purchase event. `remaining_messages` is decremented atomically
(SELECT FOR UPDATE) by QuotaService.decrement() on each successful chat turn.
A row is considered "active" when: is_active=True AND expires_at > NOW() AND remaining_messages > 0
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.package import Package, UserPayment
    from app.db.models.user import User


class ChatAddonPurchase(Base):
    __tablename__ = "chat_addon_purchases"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # NULLable after Phase 08: DSAR anonymizes user_id while keeping the row
    # for billing/accounting. ondelete=SET NULL preserves history if a user is
    # hard-deleted (DSAR clears the link explicitly).
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    package_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("packages.id", ondelete="RESTRICT"),
        nullable=False,
    )
    remaining_messages: Mapped[int] = mapped_column(Integer, nullable=False)
    tier: Mapped[str] = mapped_column(String(20), nullable=False)
    purchased_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payment_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("user_payments.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    # Relationships — lazy="raise" forces explicit loading (same pattern as package.py)
    user: Mapped[Optional["User"]] = relationship("User", lazy="raise")
    package: Mapped[Optional["Package"]] = relationship("Package", lazy="raise")
    payment: Mapped[Optional["UserPayment"]] = relationship("UserPayment", lazy="raise")


__all__ = ["ChatAddonPurchase"]
