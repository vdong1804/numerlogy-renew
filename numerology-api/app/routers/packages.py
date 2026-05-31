"""Packages router — GET /api/package and /api/package-history."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import get_current_user, get_db
from app.db.models.user import User, UserProfile
from app.db.models.package import Package, UserPackage, UserPayment
from app.db.models.download import UserDownload
from app.schemas.package import PackageOut, UserPackageOut, UserDownloadOut
from app.schemas.payment import PaymentOut

packages_router = APIRouter(prefix="/api", tags=["packages"])


@packages_router.get("/package", response_model=dict)
async def list_packages(
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all packages ordered by -created_at. Matches Django PackageList."""
    result = await db.execute(select(Package).order_by(Package.created_at.desc()))
    packages = result.scalars().all()
    return {"data": [PackageOut.model_validate(p).model_dump() for p in packages]}


@packages_router.get("/package-history", response_model=dict)
async def package_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return user payments, active package, recent downloads.

    Response shape matches Django UserPackage view exactly:
    {"data": {"user_payment": [...], "user_package": {...}, "user_download": [...]}}
    """
    # All payments with package eagerly loaded (avoid N+1)
    payments_result = await db.execute(
        select(UserPayment)
        .where(UserPayment.user_id == current_user.id)
        .options(selectinload(UserPayment.package))
    )
    user_payments = payments_result.scalars().all()

    # Active user package (is_used=True, most recent)
    pkg_result = await db.execute(
        select(UserPackage)
        .where(UserPackage.user_id == current_user.id, UserPackage.is_used == True)  # noqa: E712
        .options(selectinload(UserPackage.package))
        .order_by(UserPackage.updated_at.desc())
        .limit(1)
    )
    active_pkg = pkg_result.scalar_one_or_none()

    # Load profile for number_download on UserPackageOut
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    number_download = profile.number_download if profile else 0

    # Recent 4 paid downloads
    dl_result = await db.execute(
        select(UserDownload)
        .where(UserDownload.user_id == current_user.id, UserDownload.type == 1)
        .order_by(UserDownload.created_at.desc())
        .limit(4)
    )
    user_downloads = dl_result.scalars().all()

    # Build UserPackageOut manually (number_download comes from profile, not model)
    pkg_data = None
    if active_pkg is not None:
        pkg_data = {
            "id": active_pkg.id,
            "package": PackageOut.model_validate(active_pkg.package).model_dump()
            if active_pkg.package else None,
            "number_download": number_download,
        }

    return {
        "data": {
            "user_payment": [PaymentOut.model_validate(p).model_dump() for p in user_payments],
            "user_package": pkg_data,
            "user_download": [UserDownloadOut.model_validate(d).model_dump() for d in user_downloads],
        }
    }
