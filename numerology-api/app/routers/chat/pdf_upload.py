"""PDF upload + attach/detach endpoints for chat conversations.

POST /api/chat/conversations/{id}/upload-pdf
  - Multipart `file` (PDF), max 25 MB.
  - Validates magic bytes `%PDF-`.
  - Runs UserPdfService.ingest (hash match → parse if needed → chunk → embed).
  - Auto-attaches the resulting pdf_context_id to the conversation.

PATCH /api/chat/conversations/{id}/pdf-context
  - body: {"pdf_context_id": int | null} — attach a previously-ingested PDF or clear.

DELETE /api/chat/conversations/{id}/pdf-context
  - Clears the attachment (does NOT delete the underlying UserPdfIndex).
"""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat.user_pdf_index import UserPdfIndex
from app.db.models.user import User
from app.deps import get_current_user, get_db
from app.schemas.chat.pdf import PdfContextPatch, PdfUploadResponse
from app.services.chat.conversation_service import ConversationService
from app.services.chat.embedding_service import EmbeddingService
from app.services.chat.pdf_parser_service import PdfParseError
from app.services.chat.user_pdf_service import UserPdfService

logger = logging.getLogger(__name__)

MAX_PDF_BYTES = 25 * 1024 * 1024  # 25 MB
PDF_MAGIC = b"%PDF-"
_READ_CHUNK = 1024 * 1024  # 1 MB

pdf_upload_router = APIRouter(prefix="/api/chat/conversations", tags=["chat"])


async def _read_with_size_limit(file: UploadFile) -> bytes:
    """Stream-read the upload, bailing as soon as size > MAX_PDF_BYTES.

    Prevents loading a gigabyte attacker payload into RAM before the 413 fires
    (file.read() with no arg would buffer the whole body up-front).
    """
    buf = bytearray()
    while True:
        chunk = await file.read(_READ_CHUNK)
        if not chunk:
            break
        buf.extend(chunk)
        if len(buf) > MAX_PDF_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File too large (max {MAX_PDF_BYTES // 1024 // 1024} MB)",
            )
    return bytes(buf)


def _validate_magic_bytes(data: bytes) -> None:
    if not data.startswith(PDF_MAGIC):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Not a PDF file (missing %PDF- magic bytes)",
        )


@pdf_upload_router.post(
    "/{conversation_id}/upload-pdf",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def upload_pdf(
    conversation_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv_svc = ConversationService(db)
    conv = await conv_svc.get_owned(conversation_id, user.id)

    data = await _read_with_size_limit(file)
    _validate_magic_bytes(data)

    svc = UserPdfService(db, EmbeddingService())
    try:
        result = await svc.ingest(user.id, data, filename=file.filename)
    except PdfParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    # Auto-attach to conversation
    conv.pdf_context_id = result.pdf_index.id
    await db.flush()

    out = PdfUploadResponse(
        pdf_context_id=result.pdf_index.id,
        matched=result.matched,
        matched_report_id=result.matched_report_id,
        page_count=result.pdf_index.page_count,
        chunks_created=result.chunks_created,
        expires_at=result.pdf_index.expires_at,
    )
    return {"data": out.model_dump(mode="json")}


@pdf_upload_router.patch(
    "/{conversation_id}/pdf-context",
    response_model=dict,
)
async def patch_pdf_context(
    conversation_id: int,
    body: PdfContextPatch,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv_svc = ConversationService(db)
    conv = await conv_svc.get_owned(conversation_id, user.id)

    if body.pdf_context_id is not None:
        # Verify ownership of the referenced UserPdfIndex
        stmt = select(UserPdfIndex).where(
            UserPdfIndex.id == body.pdf_context_id,
            UserPdfIndex.user_id == user.id,
        )
        idx = (await db.execute(stmt)).scalars().first()
        if idx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="pdf_context_id not found",
            )

    conv.pdf_context_id = body.pdf_context_id
    await db.flush()
    return {"data": {"pdf_context_id": conv.pdf_context_id}}


@pdf_upload_router.delete(
    "/{conversation_id}/pdf-context",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def clear_pdf_context(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv_svc = ConversationService(db)
    conv = await conv_svc.get_owned(conversation_id, user.id)
    conv.pdf_context_id = None
    await db.flush()
