"""SQLAlchemy 2.0 models for user domain: User + UserProfile."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin

if TYPE_CHECKING:
    pass


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    last_name: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Phase 08 hardening: abuse + CAPTCHA gate
    chat_abuse_score: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, server_default="0"
    )
    chat_captcha_required: Mapped[bool] = mapped_column(
        # text("FALSE") is portable: PG accepts FALSE, SQLite parses to 0.
        Boolean, default=False, nullable=False, server_default=text("FALSE")
    )
    chat_captcha_solve_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, server_default="0"
    )
    chat_suspended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile", back_populates="user", uselist=False
    )


class UserProfile(TimestampMixin, Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    birth_day: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    number_download: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notification_prefs: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # 1-1 enforced at DB level
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_profiles_user_id"),)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")


__all__ = ["User", "UserProfile"]
