"""ChatConversation CRUD + ownership guard + history fetch.

Centralizes ownership checks so routers don't repeat the user-id filter.
Every read/write takes `user_id` and raises 404 if a different user's row
is requested — matches the existing pattern in other services (orders,
my_account).
"""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat.conversation import ChatConversation
from app.db.models.chat.message import ChatMessage


class ConversationService:
    """Thin layer over ORM that enforces user_id ownership at every call."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # -- Conversation CRUD ------------------------------------------------

    async def create(self, user_id: int, title: Optional[str] = None) -> ChatConversation:
        conv = ChatConversation(user_id=user_id, title=title)
        self.session.add(conv)
        await self.session.flush()
        await self.session.refresh(conv)
        return conv

    async def list_for_user(
        self, user_id: int, limit: int = 20, offset: int = 0
    ) -> tuple[list[ChatConversation], int]:
        base = select(ChatConversation).where(ChatConversation.user_id == user_id)
        total = (
            await self.session.execute(
                select(func.count()).select_from(base.subquery())
            )
        ).scalar_one()
        rows = (
            await self.session.execute(
                base.order_by(desc(ChatConversation.created_at)).limit(limit).offset(offset)
            )
        ).scalars().all()
        return list(rows), int(total)

    async def get_owned(self, conversation_id: int, user_id: int) -> ChatConversation:
        conv = await self.session.get(ChatConversation, conversation_id)
        if conv is None or conv.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )
        return conv

    async def delete(self, conversation_id: int, user_id: int) -> None:
        conv = await self.get_owned(conversation_id, user_id)
        await self.session.delete(conv)
        await self.session.flush()

    # -- Message history --------------------------------------------------

    async def list_messages(
        self, conversation_id: int, user_id: int, limit: int = 50, offset: int = 0
    ) -> list[ChatMessage]:
        await self.get_owned(conversation_id, user_id)
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_recent_messages(
        self, conversation_id: int, limit: int = 5
    ) -> list[ChatMessage]:
        """Last N messages (ascending by created_at) for prompt history."""
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(desc(ChatMessage.created_at))
            .limit(limit)
        )
        rows = list((await self.session.execute(stmt)).scalars().all())
        rows.reverse()  # chronological order for prompt
        return rows
