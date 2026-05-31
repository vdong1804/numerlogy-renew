"""Order endpoints — POST /api/orders, GET /api/orders/{id}, /status.

Owner-only access: get_current_user dependency + user_id scope.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.deps import get_current_user, get_db
from app.schemas.order import (
    OrderCreateRequest,
    OrderOut,
    OrderStatusOut,
)
from app.services import order_service

orders_router = APIRouter(prefix="/api/orders", tags=["orders"])


@orders_router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(
    body: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a pending order. Returns ref_code + amount + expires_at."""
    order = await order_service.create_order(db, current_user.id, body)
    return OrderOut.model_validate(order)


@orders_router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Owner-only order detail with items."""
    order = await order_service.get_order(db, order_id, user_id=current_user.id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    return OrderOut.model_validate(order)


@orders_router.get("/{order_id}/status", response_model=OrderStatusOut)
async def get_order_status(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lightweight polling endpoint — only id/ref_code/status/paid_at."""
    order = await order_service.get_order(db, order_id, user_id=current_user.id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    return OrderStatusOut(
        id=order.id,
        ref_code=order.ref_code,
        status=order.status,
        paid_at=order.paid_at,
    )
