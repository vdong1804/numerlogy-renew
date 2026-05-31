# ruff: noqa: UP045, UP017
"""Admin chatbot router (Phase 07) — KB upload, prompt editor, conversations, analytics.

All routes are mounted under ``/admin/chatbot``; the parent admin router
already enforces ``get_current_superuser`` so we don't repeat it here.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat.chat_addon_purchase import ChatAddonPurchase
from app.db.models.chat.conversation import ChatConversation
from app.db.models.chat.kb_chunk import KbChunk
from app.db.models.chat.kb_document import KbDocument
from app.db.models.chat.message import ChatMessage
from app.db.models.package import Package
from app.db.models.user import User
from app.deps import get_current_superuser, get_db
from app.schemas.chat.admin import (
    ConversationDetailOut,
    ConversationListItem,
    ConversationListOut,
    ConversationMessage,
    GrantAddonIn,
    GrantAddonOut,
    KbDocumentListOut,
    KbDocumentOut,
    KbUploadResponse,
    PromptHistoryEntry,
    PromptOut,
    PromptUpdateIn,
)
from app.services.chat.admin_kb_service import (
    AdminKbService,
    ExtractedEmpty,
    UnsupportedFileType,
)
from app.services.chat.chat_analytics_service import (
    ChatAnalyticsService,
    default_window,
)
from app.services.chat.embedding_service import EmbeddingService
from app.services.chat.kb_ingestion_service import KbIngestionService
from app.services.chat.prompt_builder import SYSTEM_PROMPT
from app.services.chat.prompt_settings_service import (
    KEY_SYSTEM_PROMPT,
    PromptSettingsService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chatbot", tags=["admin-chatbot"])

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB — bounded to keep buffer in-memory safe.
_READ_CHUNK = 1024 * 1024


async def _read_upload(file: UploadFile) -> bytes:
    """Stream-read into memory with an early 413 — caller owns the buffer."""
    buf = bytearray()
    while True:
        chunk = await file.read(_READ_CHUNK)
        if not chunk:
            break
        buf.extend(chunk)
        if len(buf) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File too large (max {MAX_UPLOAD_BYTES // 1024 // 1024} MB)",
            )
    return bytes(buf)


def _serialize_doc(doc: KbDocument, chunk_count: int = 0) -> KbDocumentOut:
    return KbDocumentOut(
        id=doc.id,
        source_type=doc.source_type,
        source_ref=doc.source_ref,
        title=doc.title,
        metadata=doc.doc_metadata or {},
        created_by=doc.created_by,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        chunk_count=chunk_count,
    )


# ---------------------------------------------------------------------------
# KB documents
# ---------------------------------------------------------------------------


@router.post("/kb/upload", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_kb_document(
    file: UploadFile = File(...),
    title: Optional[str] = Query(default=None, max_length=500),
    admin: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    data = await _read_upload(file)
    svc = AdminKbService(
        db, KbIngestionService(db, EmbeddingService())
    )
    try:
        doc = await svc.ingest_upload(
            filename=file.filename or "upload",
            file_bytes=data,
            admin_id=admin.id,
            title=title,
        )
    except UnsupportedFileType as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except ExtractedEmpty as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Refresh to populate server-default timestamps (SQLite skips RETURNING,
    # leaving created_at / updated_at unloaded otherwise).
    await db.refresh(doc)
    chunk_count = await db.scalar(
        select(func.count(KbChunk.id)).where(KbChunk.document_id == doc.id)
    ) or 0
    return KbUploadResponse(
        document=_serialize_doc(doc, chunk_count),
        chunks_created=int(chunk_count),
        file_kind=str(doc.doc_metadata.get("file_kind", "")),
        char_count=int(doc.doc_metadata.get("char_count", 0)),
    ).model_dump(mode="json")


@router.get("/kb/documents", response_model=dict)
async def list_kb_documents(
    source_type: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    base = select(KbDocument)
    if source_type:
        base = base.where(KbDocument.source_type == source_type)
    total = int((await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar_one())
    docs = (await db.execute(
        base.order_by(KbDocument.updated_at.desc()).limit(limit).offset(offset)
    )).scalars().all()

    # Batch chunk-count lookup to avoid N+1.
    counts: dict[int, int] = {}
    if docs:
        ids = [d.id for d in docs]
        rows = (await db.execute(
            select(KbChunk.document_id, func.count(KbChunk.id))
            .where(KbChunk.document_id.in_(ids))
            .group_by(KbChunk.document_id)
        )).all()
        counts = {int(did): int(c) for did, c in rows}

    items = [_serialize_doc(d, counts.get(d.id, 0)) for d in docs]
    return KbDocumentListOut(
        items=items, total=total, limit=limit, offset=offset
    ).model_dump(mode="json")


@router.delete("/kb/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kb_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(KbDocument, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")
    await db.delete(doc)  # ON DELETE CASCADE removes chunks
    await db.flush()


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------


@router.get("/prompt", response_model=dict)
async def get_prompt(db: AsyncSession = Depends(get_db)):
    svc = PromptSettingsService(db)
    row = await svc.get_current()
    if row is None:
        return PromptOut(value=SYSTEM_PROMPT, is_override=False).model_dump(mode="json")
    return PromptOut(
        value=row.value,
        is_override=True,
        version=row.version,
        updated_at=row.updated_at,
        updated_by=row.updated_by,
    ).model_dump(mode="json")


@router.put("/prompt", response_model=dict)
async def update_prompt(
    body: PromptUpdateIn,
    admin: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    svc = PromptSettingsService(db)
    row = await svc.update(KEY_SYSTEM_PROMPT, body.value, admin.id)
    return PromptOut(
        value=row.value,
        is_override=True,
        version=row.version,
        updated_at=row.updated_at,
        updated_by=row.updated_by,
    ).model_dump(mode="json")


@router.delete("/prompt", status_code=status.HTTP_204_NO_CONTENT)
async def reset_prompt(
    admin: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    svc = PromptSettingsService(db)
    await svc.delete(KEY_SYSTEM_PROMPT, deleted_by=admin.id)


@router.get("/prompt/history", response_model=dict)
async def prompt_history(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    svc = PromptSettingsService(db)
    rows = await svc.list_history(KEY_SYSTEM_PROMPT, limit=limit)
    items = [PromptHistoryEntry.model_validate(r).model_dump(mode="json") for r in rows]
    return {"items": items}


# ---------------------------------------------------------------------------
# Conversations browser
# ---------------------------------------------------------------------------


@router.get("/conversations", response_model=dict)
async def list_conversations(
    user_id: Optional[int] = Query(default=None),
    tier: Optional[str] = Query(default=None),
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    base = select(ChatConversation)
    if user_id is not None:
        base = base.where(ChatConversation.user_id == user_id)
    if date_from is not None:
        base = base.where(ChatConversation.created_at >= date_from)
    if date_to is not None:
        base = base.where(ChatConversation.created_at < date_to)
    if tier:
        # filter to conversations that have at least one message of this tier
        base = base.where(ChatConversation.id.in_(
            select(ChatMessage.conversation_id).where(ChatMessage.tier == tier)
        ))

    total = int((await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar_one())

    convs = (await db.execute(
        base.order_by(ChatConversation.created_at.desc()).limit(limit).offset(offset)
    )).scalars().all()

    counts: dict[int, int] = {}
    if convs:
        ids = [c.id for c in convs]
        rows = (await db.execute(
            select(ChatMessage.conversation_id, func.count(ChatMessage.id))
            .where(ChatMessage.conversation_id.in_(ids))
            .group_by(ChatMessage.conversation_id)
        )).all()
        counts = {int(cid): int(c) for cid, c in rows}

    items = [
        ConversationListItem(
            id=c.id,
            user_id=c.user_id,
            title=c.title,
            pdf_context_id=getattr(c, "pdf_context_id", None),
            created_at=c.created_at,
            updated_at=c.updated_at,
            message_count=counts.get(c.id, 0),
        )
        for c in convs
    ]
    return ConversationListOut(
        items=items, total=total, limit=limit, offset=offset
    ).model_dump(mode="json")


@router.get("/conversations/{conversation_id}", response_model=dict)
async def get_conversation(conversation_id: int, db: AsyncSession = Depends(get_db)):
    conv = await db.get(ChatConversation, conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="conversation not found")
    msgs = (await db.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.asc())
    )).scalars().all()
    return ConversationDetailOut(
        id=conv.id,
        user_id=conv.user_id,
        title=conv.title,
        pdf_context_id=getattr(conv, "pdf_context_id", None),
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[ConversationMessage.model_validate(m) for m in msgs],
    ).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------


@router.get("/analytics/overview", response_model=dict)
async def analytics_overview(
    days: int = Query(default=30, ge=1, le=180),
    db: AsyncSession = Depends(get_db),
):
    start, end = default_window(days)
    svc = ChatAnalyticsService(db)
    overview = await svc.overview(start, end)
    return overview.to_dict()


# ---------------------------------------------------------------------------
# Manual addon grant
# ---------------------------------------------------------------------------


@router.post("/users/{user_id}/grant-addon", response_model=dict, status_code=201)
async def grant_addon(
    user_id: int,
    body: GrantAddonIn,
    admin: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    pkg = await db.get(Package, body.package_id)
    if pkg is None:
        raise HTTPException(status_code=404, detail="package not found")
    if pkg.package_kind != "chat_addon":
        raise HTTPException(status_code=400, detail="package is not a chat_addon")

    msg_count = body.message_count or pkg.message_count
    validity = body.validity_days or pkg.validity_days
    tier = body.tier or pkg.tier
    if not msg_count or not validity or not tier:
        raise HTTPException(
            status_code=400,
            detail="package missing message_count/validity_days/tier; provide overrides",
        )

    expires = datetime.now(timezone.utc) + timedelta(days=validity)
    purchase = ChatAddonPurchase(
        user_id=user_id,
        package_id=pkg.id,
        remaining_messages=msg_count,
        tier=tier,
        expires_at=expires,
        payment_id=None,
        is_active=True,
    )
    db.add(purchase)
    await db.flush()
    await db.refresh(purchase)
    logger.info(
        "admin_grant_addon: admin=%s user=%s pkg=%s msgs=%s notes=%r",
        admin.id, user_id, pkg.id, msg_count, body.notes,
    )
    return GrantAddonOut(
        purchase_id=purchase.id,
        user_id=purchase.user_id,
        package_id=purchase.package_id,
        remaining_messages=purchase.remaining_messages,
        tier=purchase.tier,
        expires_at=purchase.expires_at,
    ).model_dump(mode="json")
