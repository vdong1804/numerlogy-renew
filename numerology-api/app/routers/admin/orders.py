"""Admin orders router — list/search orders, manual mark-paid fallback, refund, CSV export."""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi import status as http_status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.order import Order
from app.db.models.user import User
from app.deps import get_current_superuser, get_db
from app.schemas.order import OrderOut, OrderStatus
from app.services import fulfillment_service
from app.services.csv_export_service import EXPORT_ROW_LIMIT, export_orders_csv
from app.utils.query import escape_like

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin-orders"])


class RefundRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_search_stmt(
    email: Optional[str],
    ref_code: Optional[str],
    status_filter: Optional[str],
    date_from: Optional[datetime],
    date_to: Optional[datetime],
):
    """Return a SELECT statement with JOIN + conditional WHERE clauses.

    Always joins User so email ILIKE works without extra round-trip.
    """
    stmt = (
        select(Order)
        .join(User, User.id == Order.user_id)
        .options(selectinload(Order.items))
        .order_by(Order.id.desc())
    )
    if email:
        # escape_like prevents wildcard injection (%/_) from user input causing full-table scans
        stmt = stmt.where(User.email.ilike(f"%{escape_like(email)}%", escape="\\"))
    if ref_code:
        stmt = stmt.where(Order.ref_code.ilike(f"%{escape_like(ref_code)}%", escape="\\"))
    if status_filter:
        stmt = stmt.where(Order.status == status_filter)
    if date_from:
        stmt = stmt.where(Order.created_at >= date_from)
    if date_to:
        stmt = stmt.where(Order.created_at <= date_to)
    return stmt


# ---------------------------------------------------------------------------
# List / search orders — GET /admin/orders
# ---------------------------------------------------------------------------


@router.get("/orders")
async def list_orders(
    email: Optional[str] = Query(None, max_length=200, description="Filter by user email (partial match)"),
    ref_code: Optional[str] = Query(None, max_length=200, description="Filter by ref_code (partial match)"),
    status: Optional[OrderStatus] = Query(None, alias="status", description="Filter by order status"),
    date_from: Optional[datetime] = Query(None, description="Created at >= date_from (ISO 8601 with tz offset)"),
    date_to: Optional[datetime] = Query(None, description="Created at <= date_to (ISO 8601 with tz offset)"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    _admin: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Search and paginate admin orders.

    Supports filtering by email, ref_code, status, and date range.
    Requires superuser token.
    """
    stmt = _build_search_stmt(email, ref_code, status, date_from, date_to)

    # Count total matches for pagination metadata
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total: int = (await db.execute(count_stmt)).scalar_one()

    offset = (page - 1) * page_size
    items_result = await db.execute(stmt.limit(page_size).offset(offset))
    orders = items_result.scalars().all()

    return {
        "items": [OrderOut.model_validate(o).model_dump() for o in orders],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ---------------------------------------------------------------------------
# CSV export — GET /admin/orders/export.csv
# NOTE: route must be declared BEFORE /orders/{order_id} to avoid shadowing
# ---------------------------------------------------------------------------


@router.get("/orders/export.csv")
async def export_orders(
    email: Optional[str] = Query(None, max_length=200),
    ref_code: Optional[str] = Query(None, max_length=200),
    status: Optional[OrderStatus] = Query(None, alias="status"),
    # date_from/date_to: frontend sends ISO 8601 with +07:00 offset (Bangkok TZ).
    # Backend receives tz-aware datetime — no conversion needed.
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    admin: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Export filtered orders as a UTF-8 BOM CSV file.

    Max {EXPORT_ROW_LIMIT} rows — returns 400 if exceeded.
    Filename includes today's date for easy bookkeeping.
    """
    logger.info(
        "CSV export requested by admin user_id=%d filters=(email=%r ref_code=%r status=%r)",
        admin.id,
        email,
        ref_code,
        status,
    )

    try:
        csv_bytes = await export_orders_csv(
            db,
            email=email,
            ref_code=ref_code,
            status=status,
            date_from=date_from,
            date_to=date_to,
        )
    except ValueError as exc:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc))

    filename = f"orders-{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"

    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Single order detail — GET /admin/orders/{order_id}
# ---------------------------------------------------------------------------


@router.get("/orders/{order_id}")
async def get_order(
    order_id: int,
    _admin: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Order not found")
    return OrderOut.model_validate(order).model_dump()


# ---------------------------------------------------------------------------
# Manual mark-paid — POST /admin/orders/{order_id}/mark-paid
# ---------------------------------------------------------------------------


@router.post("/orders/{order_id}/mark-paid", status_code=http_status.HTTP_200_OK)
async def mark_paid(
    order_id: int,
    request: Request,
    admin: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Manual fulfillment fallback when SePay webhook missed.

    Marks the order paid (with sepay_tx_id='MANUAL-<admin_id>-<order_id>') and
    triggers the normal fulfillment pipeline. Safe to call once per order.
    """
    result = await db.execute(
        select(Order).where(Order.id == order_id).with_for_update()
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.status == "paid":
        return {"status": "already_paid", "order_id": order.id}

    if order.status not in ("pending", "expired"):
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Order in status '{order.status}' cannot be marked paid",
        )

    order.status = "paid"
    order.paid_at = datetime.now(timezone.utc)
    order.sepay_tx_id = f"MANUAL-{admin.id}-{order.id}"

    await fulfillment_service.fulfill_order(db, order)
    return {"status": "paid", "order_id": order.id, "ref_code": order.ref_code}


# ---------------------------------------------------------------------------
# Refund — POST /admin/orders/{order_id}/refund
# ---------------------------------------------------------------------------


@router.post("/orders/{order_id}/refund", status_code=http_status.HTTP_200_OK)
async def refund_order(
    order_id: int,
    body: RefundRequest,
    admin: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Refund a paid order: reverse quota/reports, send email, log note.

    Idempotent: already-refunded orders return 200 with note.
    Only orders with status='paid' can be refunded.
    """
    pre_check = await db.execute(select(Order).where(Order.id == order_id))
    existing_order = pre_check.scalar_one_or_none()
    already_refunded = existing_order is not None and existing_order.status == "refunded"

    try:
        order = await fulfillment_service.refund_order(
            db, order_id, reason=body.reason, admin_user_id=admin.id
        )
    except ValueError as exc:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc))

    result = OrderOut.model_validate(order).model_dump()
    if already_refunded:
        result["_note"] = "already refunded"
    return result
