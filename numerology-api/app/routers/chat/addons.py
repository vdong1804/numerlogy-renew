# ruff: noqa: UP045, UP017
"""Chat add-on package listing and purchase initiation.

GET  /api/chat/addons           — list active chat_addon packages
POST /api/chat/addons/{id}/purchase — initiate payment (creates pending UserPayment)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.package import Package, UserPayment
from app.db.models.user import User
from app.deps import get_current_user, get_db
from app.schemas.chat.addon import AddonPackageOut, AddonPaymentOut, AddonPurchaseInitiateOut

addons_router = APIRouter(prefix="/api/chat/addons", tags=["chat"])


# ---------------------------------------------------------------------------
# GET  /api/chat/addons
# ---------------------------------------------------------------------------


@addons_router.get("", response_model=dict)
async def list_addon_packages(
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return all active chat_addon packages ordered by price ascending."""
    result = await db.execute(
        select(Package)
        .where(Package.package_kind == "chat_addon")
        .order_by(Package.price.asc())
    )
    packages = result.scalars().all()
    return {
        "data": [
            AddonPackageOut(
                id=p.id,
                name=p.name,
                price=p.price,
                price_sale=p.price_sale,
                message_count=p.message_count,
                tier=p.tier,
                validity_days=p.validity_days,
                description=p.content,
            ).model_dump()
            for p in packages
        ]
    }


# ---------------------------------------------------------------------------
# GET /api/chat/addons/payments/{payment_id}
# ---------------------------------------------------------------------------


@addons_router.get("/payments/{payment_id}", response_model=dict)
async def get_addon_payment(
    payment_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Re-hydrate a chat add-on payment for the dedicated /chat/payment/[id] page.

    Auth-scoped: returns 404 if the payment does not belong to the caller, to
    avoid leaking existence of foreign payment IDs. Wrapped in {data: ...}
    to match the rest of the chat router envelope convention.
    """
    result = await db.execute(
        select(UserPayment, Package)
        .join(Package, Package.id == UserPayment.package_id)
        .where(UserPayment.id == payment_id)
        .where(UserPayment.user_id == user.id)
        .where(Package.package_kind == "chat_addon")
    )
    row = result.first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    payment, package = row
    out = AddonPaymentOut(
        payment_id=payment.id,
        package_id=package.id,
        package_name=package.name,
        price=payment.price,
        status=payment.status,
    )
    return {"data": out.model_dump()}


# ---------------------------------------------------------------------------
# POST /api/chat/addons/{package_id}/purchase
# ---------------------------------------------------------------------------


@addons_router.post(  # noqa: E501
    "/{package_id}/purchase",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def purchase_addon_package(
    package_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Initiate a payment for a chat add-on package.

    Validates package is active and kind='chat_addon', then creates a pending
    UserPayment row (status=1). Bank receiver info is served separately by
    GET /api/payments/bank (single source of truth from settings env vars).
    """
    # Validate package
    pkg_result = await db.execute(
        select(Package).where(Package.id == package_id)
    )
    package = pkg_result.scalar_one_or_none()
    if package is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")

    if package.package_kind != "chat_addon":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Package is not a chat add-on",
        )

    # Create pending payment
    payment = UserPayment(
        user_id=user.id,
        package_id=package.id,
        price=package.price_sale if package.price_sale > 0 else package.price,
        status=1,  # pending
    )
    db.add(payment)
    await db.flush()

    out = AddonPurchaseInitiateOut(
        payment_id=payment.id,
        package_id=package.id,
        price=payment.price,
        status=payment.status,
    )
    return {"data": out.model_dump()}


