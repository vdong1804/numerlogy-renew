# ruff: noqa: UP045, UP017
"""PromptCacheHandle — stores Gemini cached_content id + expiry metadata.

One row per unique (system_prompt + kb_chunk_ids + tier) hash. The service
layer owns creation/refresh/deletion; this model is the DB representation only.
Invalidated when KB chunks change (hook in kb_sync_service).
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PromptCacheHandle(Base):
    __tablename__ = "prompt_cache_handles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # SHA-256 hex of (system_prompt + sorted_kb_chunk_ids + tier)
    cache_key: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)

    # ID returned by Gemini client.caches.create(...)
    gemini_cache_id: Mapped[str] = mapped_column(String(255), nullable=False)

    model: Mapped[str] = mapped_column(String(50), nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
    )


__all__ = ["PromptCacheHandle"]
