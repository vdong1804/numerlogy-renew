"""ChatFeatureFlag — kill-switch + rollout-percent table (Phase 08).

`chatbot_public` is the master kill-switch — when `enabled=False` the
chat endpoints return 503 with a maintenance message. `rollout_percent`
gates access by user_id hash so launches can ramp 5% -> 25% -> 100%.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ChatFeatureFlag(Base):
    __tablename__ = "chat_feature_flags"

    flag_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    enabled: Mapped[bool] = mapped_column(
        # text("FALSE") is portable: PG accepts FALSE, SQLite parses to 0.
        Boolean, nullable=False, default=False, server_default=text("FALSE")
    )
    rollout_percent: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )


__all__ = ["ChatFeatureFlag"]
