"""ChatSystemSetting + ChatSystemSettingHistory — admin-tunable chat config (Phase 07).

`ChatSystemSetting` stores the *current* value for a config key
(e.g. ``chat_system_prompt`` override). `ChatSystemSettingHistory` is an
append-only audit log of prior versions.

Conventions:
- key is the natural identifier (uniqueness enforced at DB level)
- version is bumped on every update (1 on insert, +1 each update)
- updated_by/changed_by reference users.id, ON DELETE SET NULL for audit safety
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ChatSystemSetting(Base):
    __tablename__ = "chat_system_settings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )


class ChatSystemSettingHistory(Base):
    __tablename__ = "chat_system_settings_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    changed_by: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
    )


__all__ = ["ChatSystemSetting", "ChatSystemSettingHistory"]
