"""SQLAlchemy 2.0 models for Product and ProductItem (combo composition)."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin

if TYPE_CHECKING:
    pass


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    # 'package' | 'report' | 'combo'
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="VND")
    quota: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    renewal_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    template_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    content_codes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    meta: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (
        CheckConstraint("type IN ('package','report','combo')", name="ck_products_type"),
        CheckConstraint("price >= 0", name="ck_products_price_nonneg"),
    )


class ProductItem(Base):
    """Combo composition: combo_id -> item_id (which is another Product)."""

    __tablename__ = "product_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    combo_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    qty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __table_args__ = (
        CheckConstraint("qty >= 1", name="ck_product_items_qty"),
        UniqueConstraint("combo_id", "item_id", name="uq_product_items_combo_item"),
    )

    combo: Mapped["Product"] = relationship("Product", foreign_keys=[combo_id], lazy="raise")
    item: Mapped["Product"] = relationship("Product", foreign_keys=[item_id], lazy="raise")


__all__ = ["Product", "ProductItem"]
