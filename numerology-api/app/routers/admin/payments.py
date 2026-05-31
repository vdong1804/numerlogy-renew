"""Admin payments router — list with filter + status approval."""

from typing import Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import get_db
from app.db.models.package import UserPayment
from app.schemas.payment import PaymentOut, PaymentStatusUpdate
from app.services.payment_service import approve_payment
from app.utils.pagination import PageParams, paginate

router = APIRouter(tags=["admin-payments"])


@router.get("/payments")
async def list_payments(
    status_filter: Optional[int] = Query(default=None, alias="status"),
    page: PageParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """List all payments with optional ?status= filter."""
    stmt = select(UserPayment).options(selectinload(UserPayment.package))
    if status_filter is not None:
        stmt = stmt.where(UserPayment.status == status_filter)
    stmt = stmt.order_by(UserPayment.created_at.desc())
    items, total = await paginate(db, stmt, page)
    return {
        "items": [PaymentOut.model_validate(p).model_dump() for p in items],
        "total": total,
        "limit": page.limit,
        "offset": page.offset,
    }


@router.get("/payments/{payment_id}")
async def get_payment(payment_id: int, db: AsyncSession = Depends(get_db)):
    """Get single payment by id or 404."""
    result = await db.execute(
        select(UserPayment)
        .where(UserPayment.id == payment_id)
        .options(selectinload(UserPayment.package))
    )
    payment = result.scalar_one_or_none()
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return PaymentOut.model_validate(payment).model_dump()


@router.patch("/payments/{payment_id}/status")
async def update_payment_status(
    payment_id: int,
    body: PaymentStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update payment status. Status 1→2 triggers package grant + download quota."""
    # Only approval (1→2) has transactional side effects
    if body.status == 2:
        payment = await approve_payment(db, payment_id)
    else:
        result = await db.execute(
            select(UserPayment)
            .where(UserPayment.id == payment_id)
            .options(selectinload(UserPayment.package))
        )
        payment = result.scalar_one_or_none()
        if payment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
            )
        payment.status = body.status
        await db.flush()
        await db.refresh(payment)

    return PaymentOut.model_validate(payment).model_dump()
