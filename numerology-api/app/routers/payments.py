"""Payments router — POST /api/payments."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import get_current_user, get_db
from app.db.models.user import User
from app.db.models.package import UserPayment
from app.schemas.payment import PaymentCreate, PaymentOut

payments_router = APIRouter(prefix="/api", tags=["payments"])


@payments_router.post("/payments", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
async def create_payment(
    body: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a pending payment record (status=1). user_id forced from token."""
    payment = UserPayment(
        user_id=current_user.id,
        package_id=body.package_id,
        price=body.price,
        transaction_code=body.transaction_code,
        account_number=body.account_number,
        account_holder=body.account_holder,
        bank=body.bank,
        status=1,
    )
    db.add(payment)
    await db.flush()

    # Reload with package relationship for PaymentOut
    result = await db.execute(
        select(UserPayment)
        .where(UserPayment.id == payment.id)
        .options(selectinload(UserPayment.package))
    )
    payment = result.scalar_one()
    return PaymentOut.model_validate(payment)
