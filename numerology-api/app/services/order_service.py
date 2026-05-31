"""Order lifecycle: create, expire pending, lookup by id / ref_code.

Server-side authoritative pricing — never trust client-supplied amounts.
Order create is the only "hot" path here (<200ms target).
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.order import Order, OrderItem
from app.db.models.product import Product
from app.schemas.order import OrderCreateRequest
from app.utils.ref_code import generate_ref_code

ORDER_EXPIRY_MINUTES = 30
REF_CODE_MAX_RETRIES = 3


async def _load_active_products(
    db: AsyncSession, product_ids: list[int]
) -> dict[int, Product]:
    """Fetch active products for the given ids; missing/inactive => not in dict."""
    if not product_ids:
        return {}
    result = await db.execute(
        select(Product).where(
            Product.id.in_(product_ids), Product.is_active.is_(True)
        )
    )
    return {p.id: p for p in result.scalars().all()}


async def create_order(
    db: AsyncSession, user_id: int, body: OrderCreateRequest
) -> Order:
    """Build an order from validated items; server computes total + ref_code.

    Raises 400 if any item refers to missing/inactive product.
    """
    product_ids = [it.product_id for it in body.items]
    products = await _load_active_products(db, product_ids)

    missing = [pid for pid in product_ids if pid not in products]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product(s) not found or inactive: {missing}",
        )

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ORDER_EXPIRY_MINUTES)
    total = sum(products[it.product_id].price * it.qty for it in body.items)

    # Retry on ref_code collision (UNIQUE constraint)
    last_exc: Optional[Exception] = None
    for _ in range(REF_CODE_MAX_RETRIES):
        order = Order(
            user_id=user_id,
            ref_code=generate_ref_code(),
            total_amount=total,
            currency="VND",
            status="pending",
            payment_method="sepay",
            expires_at=expires_at,
            meta=body.input_payload,
        )
        for it in body.items:
            p = products[it.product_id]
            order.items.append(
                OrderItem(
                    product_id=p.id,
                    qty=it.qty,
                    unit_price=p.price,
                    snapshot_name=p.name,
                )
            )
        db.add(order)
        try:
            await db.flush()
            break
        except IntegrityError as exc:
            last_exc = exc
            await db.rollback()
            order = None
    else:
        # Exhausted retries
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate unique ref_code",
        ) from last_exc

    # Eager-load items for response shape
    result = await db.execute(
        select(Order)
        .where(Order.id == order.id)
        .options(selectinload(Order.items))
    )
    order = result.scalar_one()

    # Free orders (total == 0) bypass the payment gateway: mark paid + fulfill
    # immediately so the user is not parked on a useless QR page asking for 0₫.
    # Fulfillment is best-effort here — failure logs but keeps the order alive
    # so support can re-run fulfillment without the user re-purchasing.
    if total == 0:
        order.status = "paid"
        order.paid_at = datetime.now(timezone.utc)
        await db.flush()
        try:
            # Local import to avoid any future circular-import surprise
            from app.services import fulfillment_service

            await fulfillment_service.fulfill_order(db, order)
        except Exception:  # noqa: BLE001
            import logging

            logging.getLogger(__name__).exception(
                "Free-order fulfillment failed for order %s", order.id
            )

    return order


async def get_order(
    db: AsyncSession, order_id: int, user_id: Optional[int] = None
) -> Optional[Order]:
    """Fetch order with items; if user_id given, restrict to owner."""
    stmt = select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    if user_id is not None:
        stmt = stmt.where(Order.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_order_by_ref_code(db: AsyncSession, ref_code: str) -> Optional[Order]:
    result = await db.execute(
        select(Order)
        .where(Order.ref_code == ref_code)
        .options(selectinload(Order.items))
    )
    return result.scalar_one_or_none()


async def expire_pending_orders(db: AsyncSession) -> int:
    """Bulk-expire orders past their expires_at. Returns # rows updated.

    Designed to be called by a background scheduler in Phase 06.
    """
    now = datetime.now(timezone.utc)
    stmt = (
        update(Order)
        .where(Order.status == "pending", Order.expires_at < now)
        .values(status="expired")
    )
    result = await db.execute(stmt)
    return result.rowcount or 0


async def list_user_orders(
    db: AsyncSession, user_id: int, limit: int = 20, offset: int = 0
) -> Sequence[Order]:
    """Order history page support."""
    result = await db.execute(
        select(Order)
        .where(Order.user_id == user_id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()
