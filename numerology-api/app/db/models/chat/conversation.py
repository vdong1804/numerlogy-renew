"""ChatConversation — a thread of messages between a user and the bot.

`pdf_context_id` is nullable now; FK to user_pdf_contexts is wired in phase 03
when that table exists. Keeping the column shape stable avoids a second migration.
"""

from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class ChatConversation(TimestampMixin, Base):
    __tablename__ = "chat_conversations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # FK added in phase 03 when user_pdf_contexts exists
    pdf_context_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)


__all__ = ["ChatConversation"]
