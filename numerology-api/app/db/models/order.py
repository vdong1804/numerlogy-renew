"""SQLAlchemy 2.0 models for Order and OrderItem."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.db.models.product import Product


class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ref_code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True, index=True)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="VND")
    # 'pending' | 'paid' | 'cancelled' | 'expired' | 'failed'
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending", index=True)
    payment_method: Mapped[str] = mapped_column(String(32), nullable=False, default="sepay")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sepay_tx_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    meta: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','paid','cancelled','expired','failed')",
            name="ck_orders_status",
        ),
        CheckConstraint("total_amount >= 0", name="ck_orders_total_nonneg"),
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    qty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)  # snapshot
    snapshot_name: Mapped[str] = mapped_column(String(255), nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product", lazy="raise")

    __table_args__ = (
        CheckConstraint("qty >= 1", name="ck_order_items_qty"),
        CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price"),
    )


__all__ = ["Order", "OrderItem"]
