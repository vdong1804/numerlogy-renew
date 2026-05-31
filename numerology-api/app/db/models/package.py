"""SQLAlchemy 2.0 models for packages, payments, and bank accounts."""
# ruff: noqa: UP045  — Optional[X] required; str|None breaks SQLAlchemy on Python 3.9

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin

if TYPE_CHECKING:
    pass


class Package(TimestampMixin, Base):
    __tablename__ = "packages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    price_sale: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    number_download: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Chat add-on fields (added migration 0012) — NULL for pdf_download packages
    package_kind: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="pdf_download", default="pdf_download"
    )
    message_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tier: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    validity_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class UserPackage(TimestampMixin, Base):
    __tablename__ = "user_packages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    package_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False
    )
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # NULL = no expiry (lifetime). Set by fulfillment_service when package has a validity period.
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    # Relationships
    package: Mapped[Optional["Package"]] = relationship("Package", lazy="raise")


class UserPayment(TimestampMixin, Base):
    __tablename__ = "user_payments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    package_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False
    )
    price: Mapped[float] = mapped_column(Float, nullable=False)
    transaction_code: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    account_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    account_holder: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # 1=pending, 2=approved, 3=rejected
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    bank: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    package: Mapped[Optional["Package"]] = relationship("Package", lazy="raise")


class Bank(Base):
    __tablename__ = "banks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bank: Mapped[str] = mapped_column(String(255), nullable=False)
    branch: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    account_number: Mapped[str] = mapped_column(String(50), nullable=False)
    account_holder: Mapped[str] = mapped_column(String(255), nullable=False)
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)


__all__ = ["Package", "UserPackage", "UserPayment", "Bank"]
