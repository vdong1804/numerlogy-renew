"""User-scoped endpoints under /api/my/* (orders, reports, dashboard, settings)."""

import logging
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse, Response as FastResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.security import hash_password, verify_password
from app.db.models.download import UserDownload
from app.db.models.order import Order
from app.db.models.package import Package, UserPackage
from app.db.models.user import User, UserProfile
from app.db.models.user_report import UserReport
from app.deps import get_current_user, get_db
from app.schemas.order_history import (
    MyActivePackage,
    MyDashboardSummary,
    MyDownloadEntry,
    MyOrderDetail,
    MyOrderSummary,
    MyProfileOut,
    MyProfileUpdate,
    MyReportOut,
    NotificationPrefs,
)
from app.utils.pagination import PageParams, paginate
from app.utils.signed_url import verify_signed_token

logger = logging.getLogger(__name__)

_optional_bearer = HTTPBearer(auto_error=False)

my_account_router = APIRouter(prefix="/api/my", tags=["my-account"])


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@my_account_router.get("/dashboard", response_model=MyDashboardSummary)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prof_q = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = prof_q.scalar_one_or_none()
    quota_remaining = profile.number_download if profile else 0

    orders_count = (
        await db.execute(
            select(func.count(Order.id)).where(Order.user_id == current_user.id)
        )
    ).scalar_one()
    reports_count = (
        await db.execute(
            select(func.count(UserReport.id)).where(UserReport.user_id == current_user.id)
        )
    ).scalar_one()

    # Active package — is_used=True and (expires_at is NULL or > now), most recent
    now = datetime.now(timezone.utc)
    from sqlalchemy import or_

    active_pkg_q = await db.execute(
        select(UserPackage)
        .where(
            UserPackage.user_id == current_user.id,
            UserPackage.is_used == True,  # noqa: E712
            or_(UserPackage.expires_at.is_(None), UserPackage.expires_at > now),
        )
        .options(selectinload(UserPackage.package))
        .order_by(UserPackage.updated_at.desc())
        .limit(1)
    )
    active_pkg = active_pkg_q.scalar_one_or_none()

    active_package_id: Optional[int] = None
    active_package_name: Optional[str] = None
    active_package_total: Optional[int] = None
    active_package_acquired_at: Optional[datetime] = None
    active_package_expires_at: Optional[datetime] = None
    if active_pkg is not None and active_pkg.package is not None:
        active_package_id = active_pkg.package.id
        active_package_name = active_pkg.package.name
        active_package_total = int(active_pkg.package.number_download or 0)
        active_package_acquired_at = active_pkg.created_at
        active_package_expires_at = active_pkg.expires_at

    # Recent 5 orders
    recent_orders_q = await db.execute(
        select(Order)
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .limit(5)
    )
    recent_orders = [
        MyOrderSummary.model_validate(o) for o in recent_orders_q.scalars().all()
    ]

    # Recent 5 reports
    recent_reports_q = await db.execute(
        select(UserReport)
        .where(UserReport.user_id == current_user.id)
        .order_by(UserReport.generated_at.desc())
        .limit(5)
    )
    recent_reports = [
        MyReportOut.model_validate(r) for r in recent_reports_q.scalars().all()
    ]

    quota_total = active_package_total if active_package_total else quota_remaining
    quota_used = max(0, (quota_total or 0) - quota_remaining)

    return MyDashboardSummary(
        quota_total=int(quota_total or 0),
        quota_used=int(quota_used or 0),
        quota_remaining=quota_remaining,
        active_package_id=active_package_id,
        active_package_name=active_package_name,
        active_package_total=active_package_total,
        active_package_acquired_at=active_package_acquired_at,
        active_package_expires_at=active_package_expires_at,
        orders_count=int(orders_count or 0),
        reports_count=int(reports_count or 0),
        recent_orders=recent_orders,
        recent_reports=recent_reports,
    )


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------


@my_account_router.get("/orders")
async def list_my_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: PageParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Order)
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
    )
    if status_filter:
        stmt = stmt.where(Order.status == status_filter)
    items, total = await paginate(db, stmt, page)
    return {
        "items": [MyOrderSummary.model_validate(o).model_dump() for o in items],
        "total": total,
        "limit": page.limit,
        "offset": page.offset,
    }


@my_account_router.get("/orders/{order_id}", response_model=MyOrderDetail)
async def get_my_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id, Order.user_id == current_user.id)
        .options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return MyOrderDetail.model_validate(order)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


@my_account_router.get("/reports")
async def list_my_reports(
    page: PageParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(UserReport)
        .where(UserReport.user_id == current_user.id)
        .order_by(UserReport.generated_at.desc())
    )
    items, total = await paginate(db, stmt, page)
    return {
        "items": [MyReportOut.model_validate(r).model_dump() for r in items],
        "total": total,
        "limit": page.limit,
        "offset": page.offset,
    }


@my_account_router.get("/reports/{report_id}/download")
async def download_report(
    report_id: int,
    token: Optional[str] = Query(None, description="Signed HMAC download token (7-day, no login required)"),
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_optional_bearer),
):
    """Stream the report PDF.

    Auth priority:
    1. ?token=<signed_hmac>  — no login required (from email link)
    2. Bearer JWT            — normal authenticated access

    Uses pdf_path from DB (no path traversal possible).
    """
    verified_report_id: Optional[int] = None

    # Path 1: signed token from email link
    if token:
        verified_report_id = verify_signed_token(token)
        if verified_report_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired download token",
            )
        if verified_report_id != report_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token does not match report",
            )
        # Fetch report by ID only (no user ownership check — token is the auth)
        result = await db.execute(select(UserReport).where(UserReport.id == report_id))
        report = result.scalar_one_or_none()

    # Path 2: Bearer JWT fallback
    elif credentials is not None:
        from app.core.security import decode_token
        from jose import JWTError

        try:
            payload = decode_token(credentials.credentials)
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalid or expired")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_id = int(user_id_str)

        result = await db.execute(
            select(UserReport).where(UserReport.id == report_id, UserReport.user_id == user_id)
        )
        report = result.scalar_one_or_none()

    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: provide ?token= or Bearer JWT",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    if report.pdf_path.startswith("REFUNDED/"):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Report has been refunded and is no longer available")

    # Path traversal guard: resolve absolute path and verify it stays within media_root
    media_root_abs = os.path.realpath(settings.media_root)
    abs_path = os.path.realpath(os.path.join(media_root_abs, report.pdf_path))
    if os.path.commonpath([abs_path, media_root_abs]) != media_root_abs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid report path")

    if not os.path.isfile(abs_path):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Report file no longer available")

    report.download_count = (report.download_count or 0) + 1
    report.last_downloaded_at = datetime.now(timezone.utc)
    await db.flush()

    return FileResponse(
        abs_path,
        media_type="application/pdf",
        filename=f"report-{report.id}.pdf",
    )


# ---------------------------------------------------------------------------
# Password change
# ---------------------------------------------------------------------------


@my_account_router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    old = (body or {}).get("old_password") or ""
    new = (body or {}).get("new_password") or ""
    if not new or len(new) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be ≥ 8 characters",
        )
    if not current_user.hashed_password or not verify_password(
        old, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect"
        )
    current_user.hashed_password = hash_password(new)
    await db.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Notification preferences
# ---------------------------------------------------------------------------


async def _get_or_create_profile(db: AsyncSession, user: User) -> UserProfile:
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = UserProfile(
            user_id=user.id,
            name=f"{user.first_name} {user.last_name}".strip() or user.email,
        )
        db.add(profile)
        await db.flush()
    return profile


@my_account_router.get("/settings/notifications", response_model=NotificationPrefs)
async def get_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_profile(db, current_user)
    return NotificationPrefs(**(profile.notification_prefs or {}))


@my_account_router.put("/settings/notifications", response_model=NotificationPrefs)
async def update_notifications(
    body: NotificationPrefs,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_profile(db, current_user)
    profile.notification_prefs = body.model_dump()
    await db.flush()
    return body


# ---------------------------------------------------------------------------
# Profile (mirror /api/profile under /api/my namespace)
# ---------------------------------------------------------------------------


def _profile_payload(user: User, profile: UserProfile) -> MyProfileOut:
    return MyProfileOut(
        id=user.id,
        email=user.email,
        first_name=user.first_name or "",
        last_name=user.last_name or "",
        name=profile.name or f"{user.first_name} {user.last_name}".strip(),
        birth_day=profile.birth_day,
        address=profile.address,
        phone=profile.phone,
        number_download=profile.number_download or 0,
        notification_prefs=profile.notification_prefs or {},
    )


@my_account_router.get("/profile", response_model=MyProfileOut)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_profile(db, current_user)
    return _profile_payload(current_user, profile)


@my_account_router.put("/profile", response_model=MyProfileOut)
async def update_my_profile(
    body: MyProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_profile(db, current_user)
    for field, value in body.model_dump(exclude_none=True).items():
        # `gender` not yet a real column — skip silently to keep API tolerant
        if not hasattr(profile, field):
            continue
        setattr(profile, field, value)
    await db.flush()
    await db.refresh(profile)
    return _profile_payload(current_user, profile)


# ---------------------------------------------------------------------------
# Active packages — phase-03 spec
# ---------------------------------------------------------------------------


@my_account_router.get("/packages", response_model=list[MyActivePackage])
async def list_my_packages(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """All packages owned by user. Active = is_used AND not expired."""
    result = await db.execute(
        select(UserPackage)
        .where(UserPackage.user_id == current_user.id)
        .options(selectinload(UserPackage.package))
        .order_by(UserPackage.created_at.desc())
    )
    rows = result.scalars().all()

    profile = await _get_or_create_profile(db, current_user)
    quota_remaining = int(profile.number_download or 0)

    now = datetime.now(timezone.utc)
    out: list[MyActivePackage] = []
    for up in rows:
        pkg: Optional[Package] = up.package
        if pkg is None:
            continue
        total = int(pkg.number_download or 0)
        not_expired = up.expires_at is None or up.expires_at > now
        is_active = bool(up.is_used) and not_expired
        out.append(
            MyActivePackage(
                id=up.id,
                package_id=pkg.id,
                name=pkg.name,
                quota_total=total,
                quota_remaining=quota_remaining if is_active else 0,
                acquired_at=up.created_at,
                expires_at=up.expires_at,
                is_active=is_active,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Download history
# ---------------------------------------------------------------------------


@my_account_router.get("/downloads")
async def list_my_downloads(
    type_filter: Optional[int] = Query(None, alias="type", ge=0, le=1),
    page: PageParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(UserDownload)
        .where(UserDownload.user_id == current_user.id)
        .order_by(UserDownload.created_at.desc())
    )
    if type_filter is not None:
        stmt = stmt.where(UserDownload.type == type_filter)
    items, total = await paginate(db, stmt, page)
    return {
        "items": [MyDownloadEntry.model_validate(d).model_dump() for d in items],
        "total": total,
        "limit": page.limit,
        "offset": page.offset,
    }


# ---------------------------------------------------------------------------
# Invoice PDF
# ---------------------------------------------------------------------------


@my_account_router.get("/orders/{order_id}/invoice")
async def download_invoice(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Render invoice PDF for a paid order.

    Caches PDF at media_root/invoices/{order_id}.pdf to avoid repeated wkhtmltopdf calls.
    """
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id, Order.user_id == current_user.id)
        .options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.status != "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice is only available for paid orders",
        )

    invoices_dir = os.path.join(settings.media_root, "invoices")
    os.makedirs(invoices_dir, exist_ok=True)
    cache_path = os.path.join(invoices_dir, f"order-{order.id}.pdf")

    if not os.path.isfile(cache_path):
        try:
            from app.utils.pdf import render_pdf

            ctx = {
                "order": {
                    "id": order.id,
                    "ref_code": order.ref_code,
                    "total_amount": order.total_amount,
                    "currency": order.currency,
                    "status": order.status,
                    "paid_at": order.paid_at.isoformat() if order.paid_at else None,
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                },
                "items": [
                    {
                        "snapshot_name": it.snapshot_name,
                        "qty": it.qty,
                        "unit_price": it.unit_price,
                        "subtotal": it.qty * it.unit_price,
                    }
                    for it in order.items
                ],
                "customer": {
                    "email": current_user.email,
                    "name": f"{current_user.first_name} {current_user.last_name}".strip()
                    or current_user.email,
                },
                "company": {
                    "name": "Nhân Sinh Quan",
                    "site": "nhansinhquan.vn",
                },
            }
            pdf_bytes = await render_pdf("invoice-order.html", ctx)
            with open(cache_path, "wb") as fh:
                fh.write(pdf_bytes)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Invoice PDF render failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not generate invoice",
            ) from exc

    return FileResponse(
        cache_path,
        media_type="application/pdf",
        filename=f"invoice-{order.ref_code}.pdf",
    )
