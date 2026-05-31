"""Payment approval service — transactional status transition logic."""

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.package import Package, UserPackage, UserPayment
from app.db.models.user import UserProfile


async def approve_payment(db: AsyncSession, payment_id: int) -> UserPayment:
    """Transition payment 1→2 (pending→approved).

    Branches on package.package_kind:
    - 'chat_addon'  → calls addon_fulfillment.fulfill_chat_addon (creates ChatAddonPurchase)
    - 'pdf_download' / default → existing UserPackage + quota grant logic

    In a single transaction:
    1. Validate payment exists and is pending (status=1).
    2. Dispatch to kind-specific fulfillment.
    3. Set payment.status = 2.

    Raises:
        404 if payment not found.
        400 if payment not in pending state or package not found.
    """
    result = await db.execute(
        select(UserPayment)
        .where(UserPayment.id == payment_id)
        .options(selectinload(UserPayment.package))
    )
    payment = result.scalar_one_or_none()
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    if payment.status != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment already processed (status={payment.status})",
        )

    # Load package
    pkg_result = await db.execute(select(Package).where(Package.id == payment.package_id))
    package = pkg_result.scalar_one_or_none()
    if package is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Package not found")

    # Dispatch by package kind
    if package.package_kind == "chat_addon":
        await _fulfill_chat_addon_payment(db, payment, package)
    else:
        await _fulfill_pdf_download_payment(db, payment, package)

    # Approve payment
    payment.status = 2
    await db.flush()

    # Reload with package relationship for PaymentOut serialization
    result2 = await db.execute(
        select(UserPayment)
        .where(UserPayment.id == payment.id)
        .options(selectinload(UserPayment.package))
    )
    return result2.scalar_one()


# ---------------------------------------------------------------------------
# Private dispatch helpers
# ---------------------------------------------------------------------------


async def _fulfill_chat_addon_payment(
    db: AsyncSession, payment: UserPayment, package: Package
) -> None:
    """Create a ChatAddonPurchase row for an approved chat addon payment."""
    from app.services.chat.addon_fulfillment import fulfill_chat_addon

    await fulfill_chat_addon(db, user_id=payment.user_id, package=package, payment_id=payment.id)


async def _fulfill_pdf_download_payment(
    db: AsyncSession, payment: UserPayment, package: Package
) -> None:
    """Original fulfillment: grant UserPackage + increment download quota."""
    # Deactivate old active packages for this user
    await db.execute(
        update(UserPackage)
        .where(UserPackage.user_id == payment.user_id, UserPackage.is_used == True)  # noqa: E712
        .values(is_used=False)
    )

    # Create new active user package
    new_pkg = UserPackage(user_id=payment.user_id, package_id=package.id, is_used=True)
    db.add(new_pkg)

    # Increment download quota
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == payment.user_id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile:
        profile.number_download = profile.number_download + package.number_download

    await db.flush()
