# ruff: noqa: UP045, UP017
"""Pydantic schemas for the Phase 07 admin chatbot endpoints."""

from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# KB documents
# ---------------------------------------------------------------------------


class KbDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_type: str
    source_ref: str
    title: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    chunk_count: int = 0


class KbDocumentListOut(BaseModel):
    items: list[KbDocumentOut]
    total: int
    limit: int
    offset: int


class KbUploadResponse(BaseModel):
    document: KbDocumentOut
    chunks_created: int
    file_kind: str
    char_count: int


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------


class PromptOut(BaseModel):
    """Current effective prompt — either the DB override or the in-code default."""

    value: str
    is_override: bool
    version: Optional[int] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None


class PromptUpdateIn(BaseModel):
    value: str = Field(min_length=1, max_length=20_000)


class PromptHistoryEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    value: str
    version: int
    changed_by: Optional[int] = None
    changed_at: datetime


# ---------------------------------------------------------------------------
# Conversations browser
# ---------------------------------------------------------------------------


class ConversationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: Optional[str] = None
    pdf_context_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ConversationListOut(BaseModel):
    items: list[ConversationListItem]
    total: int
    limit: int
    offset: int


class ConversationMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    model_used: Optional[str] = None
    tier: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    citations: list[Any] = Field(default_factory=list)
    created_at: datetime


class ConversationDetailOut(BaseModel):
    id: int
    user_id: int
    title: Optional[str] = None
    pdf_context_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    messages: list[ConversationMessage]


# ---------------------------------------------------------------------------
# Manual addon grant
# ---------------------------------------------------------------------------


class GrantAddonIn(BaseModel):
    package_id: int
    notes: Optional[str] = Field(default=None, max_length=500)
    # Override if package's message_count/validity_days need a manual tweak
    message_count: Optional[int] = Field(default=None, ge=1)
    validity_days: Optional[int] = Field(default=None, ge=1, le=365)
    tier: Optional[Literal["free", "paid"]] = None


class GrantAddonOut(BaseModel):
    purchase_id: int
    user_id: int
    package_id: int
    remaining_messages: int
    tier: str
    expires_at: datetime


# ---------------------------------------------------------------------------
# Analytics — pass-through dict; structured for OpenAPI docs only
# ---------------------------------------------------------------------------


class AnalyticsRequest(BaseModel):
    start: Optional[date] = None
    end: Optional[date] = None


__all__ = [
    "KbDocumentOut",
    "KbDocumentListOut",
    "KbUploadResponse",
    "PromptOut",
    "PromptUpdateIn",
    "PromptHistoryEntry",
    "ConversationListItem",
    "ConversationListOut",
    "ConversationMessage",
    "ConversationDetailOut",
    "GrantAddonIn",
    "GrantAddonOut",
    "AnalyticsRequest",
]
