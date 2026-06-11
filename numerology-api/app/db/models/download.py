"""SQLAlchemy 2.0 model for user download tracking."""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserDownload(Base):
    __tablename__ = "user_downloads"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # Nullable FK — row kept when user deleted (SET NULL)
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    birth_day: Mapped[str] = mapped_column(String(20), nullable=False)
    birth_time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    job: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    # 0=free, 1=paid — SMALLINT with CHECK constraint
    type: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("type IN (0, 1)", name="ck_user_downloads_type"),
    )


__all__ = ["UserDownload"]
