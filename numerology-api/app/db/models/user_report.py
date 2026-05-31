"""SQLAlchemy 2.0 model for UserReport (generated PDFs)."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.product import Product
    from app.db.models.order import Order


class UserReport(Base):
    __tablename__ = "user_reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # NULL for lead-magnet free reports (no order)
    order_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    pdf_path: Mapped[str] = mapped_column(String(512), nullable=False)
    # SHA256 hex digest of the PDF file content — populated lazily on first
    # download or via scripts/backfill_pdf_hashes.py. Used by chatbot to match
    # uploaded PDFs against system-generated ones without re-parsing.
    file_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=True
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    input_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    download_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_downloaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    product: Mapped["Product"] = relationship("Product", lazy="raise")
    order: Mapped[Optional["Order"]] = relationship("Order", lazy="raise")


__all__ = ["UserReport"]
