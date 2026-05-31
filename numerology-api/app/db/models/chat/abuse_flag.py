# ruff: noqa: UP045, UP017
"""ChatAbuseFlag — append-only abuse incident log (Phase 08).

One row per detected pattern hit. Job `detect_chat_abuse` writes rows here and
increments `users.chat_abuse_score`. Admin reviews flags; setting
`resolution='cleared'` is a manual override.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

_JSONB_OR_JSON = JSONB().with_variant(JSON(), "sqlite")


class ChatAbuseFlag(Base):
    __tablename__ = "chat_abuse_flags"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    # IPv4/IPv6 — nullable when no IP known (e.g. server-side aggregation row).
    ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    # 'rapid_quota_cycle' | 'prompt_injection' | 'identical_burst' |
    # 'quota_exhaustion_grief' | 'pdf_upload_spam'
    pattern: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    details: Mapped[Optional[dict]] = mapped_column(_JSONB_OR_JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # 'banned' | 'captcha_required' | 'cleared'
    resolution: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)


__all__ = ["ChatAbuseFlag"]
