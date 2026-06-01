"""Payments router — POST /api/payments + GET /api/payments/bank (SePay display info)."""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.deps import get_current_user, get_db
from app.db.models.user import User
from app.db.models.package import UserPayment
from app.schemas.payment import PaymentCreate, PaymentOut

payments_router = APIRouter(prefix="/api", tags=["payments"])


class BankInfoOut(BaseModel):
    """Public bank receiver info for displaying SePay transfer instructions.

    Safe to expose without auth — these are account numbers users transfer to.
    Source of truth: env vars (BANK_*) consumed by SePay reconcile + webhook.
    """

    account_number: str
    account_holder: str
    bank_code: str
    bank_name: str


@payments_router.get("/payments/bank", response_model=BankInfoOut)
async def get_bank_info() -> BankInfoOut:
    """Return the bank account info used for SePay transfers.

    Public endpoint — used by frontend checkout + chat upgrade pages to
    render a single canonical SePayPaymentBlock.
    """
    return BankInfoOut(
        account_number=settings.bank_account_number,
        account_holder=settings.bank_account_holder,
        bank_code=settings.bank_code,
        bank_name=settings.bank_name,
    )


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
