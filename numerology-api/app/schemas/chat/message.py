"""Message DTOs — request body + response + citation payload."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    pdf_context_id: Optional[int] = None  # noqa: UP045  # explicit override; falls back to conv.pdf_context_id
    # Phase 08: Turnstile token, only sent when user.chat_captcha_required=True.
    captcha_token: Optional[str] = None  # noqa: UP045


class Citation(BaseModel):
    index: int  # the [N] number used in the answer text
    chunk_id: int
    document_id: int
    source_type: str
    source_ref: str
    title: Optional[str] = None  # noqa: UP045
    score: float


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str  # 'user' | 'assistant' | 'system'
    content: str
    citations: list[Citation] = []
    model_used: Optional[str] = None  # noqa: UP045
    tier: Optional[str] = None  # noqa: UP045
    input_tokens: int = 0
    output_tokens: int = 0
    created_at: datetime
    from_cache: bool = False
