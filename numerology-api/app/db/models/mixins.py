"""Shared SQLAlchemy 2.0 mixins for all ORM models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Adds created_at / updated_at columns with auto-management."""

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )


class NumerologyContentMixin:
    """Common columns shared by ~22 numerology content tables.

    Each subclass must declare __tablename__.
    Adds: id PK, code (indexed + unique), value (nullable),
          title, content (Text), number_page (nullable int).
    """

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(255), index=True, unique=True, nullable=False)
    value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    number_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
