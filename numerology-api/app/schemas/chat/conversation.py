"""Conversation DTOs — create, list, detail."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime


class ConversationListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
