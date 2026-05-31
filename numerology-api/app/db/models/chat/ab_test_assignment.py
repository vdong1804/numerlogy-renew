"""ChatAbTestAssignment — deterministic user->variant mapping (Phase 08).

Assigned on first chat turn from `ab_test_service.get_or_assign_variant`.
Variant string is consumed by `prompt_builder` to swap in variant-specific
system prompts loaded from `chat_system_settings`.
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ChatAbTestAssignment(Base):
    __tablename__ = "chat_ab_test_assignments"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # 'control' | 'variant_a' | 'variant_b'
    variant: Mapped[str] = mapped_column(String(50), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
    )


__all__ = ["ChatAbTestAssignment"]
