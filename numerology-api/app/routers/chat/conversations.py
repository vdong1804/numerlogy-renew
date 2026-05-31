"""Conversation CRUD endpoints — owned by the authenticated user."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.deps import get_current_user, get_db
from app.schemas.chat.conversation import (
    ConversationCreate,
    ConversationListOut,
    ConversationOut,
)
from app.services.chat.conversation_service import ConversationService
from app.utils.pagination import PageParams

conversations_router = APIRouter(prefix="/api/chat/conversations", tags=["chat"])


@conversations_router.post(
    "", response_model=dict, status_code=status.HTTP_201_CREATED
)
async def create_conversation(
    body: ConversationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ConversationService(db)
    conv = await svc.create(user.id, body.title)
    return {"data": ConversationOut.model_validate(conv).model_dump()}


@conversations_router.get("", response_model=dict)
async def list_conversations(
    page: PageParams = Depends(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ConversationService(db)
    items, total = await svc.list_for_user(user.id, limit=page.limit, offset=page.offset)
    return {
        "data": [ConversationListOut.model_validate(c).model_dump() for c in items],
        "total": total,
        "limit": page.limit,
        "offset": page.offset,
    }


@conversations_router.get("/{conversation_id}", response_model=dict)
async def get_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ConversationService(db)
    conv = await svc.get_owned(conversation_id, user.id)
    return {"data": ConversationOut.model_validate(conv).model_dump()}


@conversations_router.delete(
    "/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ConversationService(db)
    await svc.delete(conversation_id, user.id)
