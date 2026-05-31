"""Pydantic DTOs for chat routes (Phase 02)."""

from app.schemas.chat.conversation import (
    ConversationCreate,
    ConversationListOut,
    ConversationOut,
)
from app.schemas.chat.message import Citation, MessageIn, MessageOut
from app.schemas.chat.pdf import PdfContextPatch, PdfUploadResponse
from app.schemas.chat.retrieval import RetrievedChunk

__all__ = [
    "ConversationCreate",
    "ConversationOut",
    "ConversationListOut",
    "MessageIn",
    "MessageOut",
    "Citation",
    "PdfUploadResponse",
    "PdfContextPatch",
    "RetrievedChunk",
]
