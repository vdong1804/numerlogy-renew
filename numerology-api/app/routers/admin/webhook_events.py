"""Admin webhook events log router."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.webhook_event import WebhookEvent
from app.deps import get_db
from app.utils.pagination import PageParams, paginate

router = APIRouter(tags=["admin-webhook-events"])


@router.get("/webhook-events")
async def list_events(
    status_filter: Optional[str] = Query(None, alias="status"),
    provider: Optional[str] = Query(None),
    page: PageParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(WebhookEvent).order_by(WebhookEvent.id.desc())
    if status_filter:
        stmt = stmt.where(WebhookEvent.status == status_filter)
    if provider:
        stmt = stmt.where(WebhookEvent.provider == provider)
    items, total = await paginate(db, stmt, page)
    return {
        "items": [
            {
                "id": e.id,
                "provider": e.provider,
                "sepay_tx_id": e.sepay_tx_id,
                "status": e.status,
                "order_id": e.order_id,
                "ref_code": e.ref_code,
                "amount": e.amount,
                "error_message": e.error_message,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "raw_payload": e.raw_payload,
            }
            for e in items
        ],
        "total": total,
        "limit": page.limit,
        "offset": page.offset,
    }
