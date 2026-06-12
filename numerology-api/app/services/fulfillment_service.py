"""Post-payment fulfillment: grant quota / render PDF for an order's items.

Idempotency — fulfill_order is intended to be called at most once per order,
but the helpers are written so a second call is safe (uses upsert / counted
checks). The webhook layer guards against duplicate processing.
"""

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.numerology import calculate_numerology_numbers
from app.db.models.order import Order
from app.db.models.product import Product, ProductItem
from app.db.models.user_report import UserReport
from app.services.cover_generator import get_cover_background
from app.services.report_charts import build_charts
from app.utils.pdf import render_pdf

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


async def fulfill_order(db: AsyncSession, order: Order) -> list[UserReport]:
    """Dispatch each order_item to its type-specific fulfillment.

    Returns the list of UserReport rows created (may be empty for pure-package
    orders). Raises on rendering / DB failure so the caller can decide what to
    do (the webhook layer catches and marks the event as 'error').
    """
    # Ensure items + their products are loaded
    result = await db.execute(
        select(Order).where(Order.id == order.id).options(selectinload(Order.items))
    )
    order = result.scalar_one()

    product_ids = [it.product_id for it in order.items]
    products_q = await db.execute(select(Product).where(Product.id.in_(product_ids)))
    products = {p.id: p for p in products_q.scalars().all()}

    created_reports: list[UserReport] = []
    for it in order.items:
        product = products[it.product_id]
        reports = await _fulfill_item(db, order, product, qty=it.qty)
        created_reports.extend(reports)
    await db.flush()

    # Enqueue order_paid email (best-effort, never block fulfillment on it)
    try:
        from app.db.models.user import User
        from app.services import email_outbox_service
        from app.utils.signed_url import make_signed_token

        user_q = await db.execute(select(User).where(User.id == order.user_id))
        user = user_q.scalar_one_or_none()
        if user is not None:
            frontend_url = settings.frontend_url.rstrip("/")
            # Build signed download links for report-type products
            report_links = [
                {
                    "report_id": r.id,
                    "name": f"Báo cáo #{r.id}",
                    "signed_token": make_signed_token(r.id),
                }
                for r in created_reports
            ]
            await email_outbox_service.enqueue(
                db,
                to_email=user.email,
                template="order-paid",
                payload={
                    "ref_code": order.ref_code,
                    "order_id": order.id,
                    "total_amount_vnd": f"{order.total_amount:,}".replace(",", "."),
                    "payment_method": order.payment_method,
                    "frontend_url": frontend_url,
                    "base_url": frontend_url,
                    "reports": report_links,
                },
                user_id=user.id,
            )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to enqueue order_paid email for order %s", order.id)

    return created_reports


# ---------------------------------------------------------------------------
# Item dispatch
# ---------------------------------------------------------------------------


async def _fulfill_item(
    db: AsyncSession, order: Order, product: Product, qty: int
) -> list[UserReport]:
    if product.type == "package":
        await _fulfill_package(db, order, product, qty=qty)
        return []
    if product.type == "report":
        reports = []
        for _ in range(qty):
            r = await _fulfill_report(db, order, product)
            reports.append(r)
        return reports
    if product.type == "combo":
        return await _fulfill_combo(db, order, product, qty=qty)
    logger.warning("Unknown product type for fulfillment: %s", product.type)
    return []


# ---------------------------------------------------------------------------
# Package — grants download quota.
# Note: legacy user_packages / user_profiles.number_download is the source of
# truth for the existing PDF download flow, so we increment that to stay
# compatible. A dedicated subscriptions table is a Phase 06 concern.
# ---------------------------------------------------------------------------


async def _fulfill_package(
    db: AsyncSession, order: Order, product: Product, qty: int = 1
) -> None:
    from app.db.models.package import Package as LegacyPackage, UserPackage
    from app.db.models.user import UserProfile

    quota = (product.quota or 0) * qty
    if quota <= 0:
        return

    # Best-effort link to legacy Package row (match by name) so downstream
    # views that still query `user_packages` continue to work.
    legacy_pkg = None
    legacy_q = await db.execute(
        select(LegacyPackage).where(LegacyPackage.name == product.name).limit(1)
    )
    legacy_pkg = legacy_q.scalar_one_or_none()
    if legacy_pkg is None:
        # Create a thin legacy row to satisfy FK
        legacy_pkg = LegacyPackage(
            name=product.name,
            price=float(product.price),
            price_sale=float(product.price),
            number_download=product.quota or 0,
            content=product.description or "",
        )
        db.add(legacy_pkg)
        await db.flush()

    # Compute expiry from product.renewal_days (NULL = lifetime).
    # Use paid_at as anchor; fall back to now for safety.
    expires_at: Optional[datetime] = None
    if product.renewal_days and product.renewal_days > 0:
        anchor = order.paid_at or datetime.now(timezone.utc)
        expires_at = anchor + timedelta(days=int(product.renewal_days))

    up = UserPackage(
        user_id=order.user_id,
        package_id=legacy_pkg.id,
        is_used=True,
        expires_at=expires_at,
    )
    db.add(up)

    # Increment profile-level quota that gates PDF downloads in legacy code.
    prof_q = await db.execute(
        select(UserProfile).where(UserProfile.user_id == order.user_id)
    )
    profile = prof_q.scalar_one_or_none()
    if profile is not None:
        profile.number_download = (profile.number_download or 0) + quota

    await db.flush()


# ---------------------------------------------------------------------------
# Report — render a PDF, persist a user_reports row.
# ---------------------------------------------------------------------------


async def _fulfill_report(
    db: AsyncSession, order: Optional[Order], product: Product, *, user_id: Optional[int] = None
) -> UserReport:
    if order is not None:
        user_id = order.user_id

    if user_id is None:
        raise ValueError("Either order or user_id must be provided")

    input_payload: dict = {}
    if order is not None and isinstance(order.meta, dict):
        input_payload = dict(order.meta)

    pdf_path = await _render_report_pdf(
        db=db,
        template_name=product.template_name or "invoice.html",
        content_codes=product.content_codes or [],
        input_payload=input_payload,
        order_id=order.id if order else None,
        user_id=user_id,
    )

    report = UserReport(
        user_id=user_id,
        order_id=order.id if order else None,
        product_id=product.id,
        pdf_path=pdf_path,
        input_payload=input_payload,
    )
    db.add(report)
    await db.flush()
    return report


# ---------------------------------------------------------------------------
# Combo — expand and recurse.
# ---------------------------------------------------------------------------


async def _fulfill_combo(
    db: AsyncSession, order: Order, combo: Product, qty: int
) -> list[UserReport]:
    q = await db.execute(
        select(ProductItem).where(ProductItem.combo_id == combo.id)
    )
    components: Iterable[ProductItem] = q.scalars().all()

    products_q = await db.execute(
        select(Product).where(Product.id.in_([c.item_id for c in components]))
    )
    products_by_id = {p.id: p for p in products_q.scalars().all()}

    reports: list[UserReport] = []
    for comp in components:
        sub = products_by_id[comp.item_id]
        sub_reports = await _fulfill_item(db, order, sub, qty=comp.qty * qty)
        reports.extend(sub_reports)
    return reports


# ---------------------------------------------------------------------------
# PDF rendering
# ---------------------------------------------------------------------------


async def _render_report_pdf(
    *,
    db: AsyncSession,
    template_name: str,
    content_codes: list[str],
    input_payload: dict,
    order_id: Optional[int],
    user_id: int,
) -> str:
    """Render report PDF via Jinja2 + wkhtmltopdf and persist to media root.

    Returns the relative path (under media_root). Caller stores it.
    """
    # Look up content rows for each requested code. We re-use the existing
    # numerology content tables — only those that match `content_codes`.
    contents = await _fetch_content_by_codes(db, content_codes)

    context = {
        "input": input_payload,
        "content": contents,
        "order_id": order_id,
        "user_id": user_id,
        "cover_bg": await _resolve_cover_bg(input_payload),
        "charts": _resolve_charts(input_payload),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    # Try-render; if the requested template is missing we fall back to the
    # legacy invoice.html so we never crash a paid fulfillment.
    try:
        pdf_bytes = await render_pdf(f"reports/{template_name}", context)
    except Exception:  # noqa: BLE001
        logger.warning(
            "Falling back to invoice.html for missing template %s", template_name
        )
        pdf_bytes = await render_pdf("invoice.html", context)

    # Write PDF under MEDIA_ROOT/reports/{yyyymm}/{uuid}.pdf
    rel_dir = Path("reports") / datetime.now(timezone.utc).strftime("%Y%m")
    abs_dir = Path(settings.media_root) / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.pdf"
    abs_path = abs_dir / filename
    abs_path.write_bytes(pdf_bytes)
    return str(rel_dir / filename).replace(os.sep, "/")


async def _resolve_cover_bg(input_payload: dict) -> Optional[str]:
    """Compute Số chủ đạo from the order input → per-user cover background.

    Fully guarded: any missing/invalid input → None (cover falls back to the
    static art / gradient). Never raises — must not block fulfillment.
    """
    try:
        name = input_payload.get("name") or input_payload.get("full_name") or ""
        birth_day = "".join(c for c in str(input_payload.get("birth_day", "")) if c.isdigit())
        if not name or not birth_day:
            return None
        so_chu_dao = calculate_numerology_numbers(birth_day, name)["so_chu_dao"]
        return await get_cover_background(so_chu_dao)
    except Exception as exc:  # noqa: BLE001 — fail-safe
        logger.warning("cover bg resolution skipped: %s", exc)
        return None


def _resolve_charts(input_payload: dict) -> Optional[dict]:
    """Compute the 4 cosmic charts from the order input (name + birth_day).

    Fully guarded: missing/invalid input → None so the template skips charts.
    build_charts is pure CPU (no DB/IO) and fast → called synchronously. Never
    raises — must not block fulfillment.
    """
    try:
        name = input_payload.get("name") or input_payload.get("full_name") or ""
        birth_day = "".join(c for c in str(input_payload.get("birth_day", "")) if c.isdigit())
        if not name or not birth_day:
            return None
        calc = calculate_numerology_numbers(birth_day, name)
        return build_charts(calc, birth_day)
    except Exception as exc:  # noqa: BLE001 — fail-safe
        logger.warning("chart resolution skipped: %s", exc)
        return None


async def _fetch_content_by_codes(
    db: AsyncSession, codes: list[str]
) -> dict[str, dict]:
    """Look up numerology content rows keyed by `code`. Empty/missing -> skip.

    Returns ``{code: {title, content, value, ...}}`` so templates can do
    ``{{ content.main_number.content | safe }}``.
    """
    if not codes:
        return {}

    # The 22 content tables share `code` and `content` columns. We avoid a
    # hard import of every model by going through Base metadata.
    from app.db.base import Base

    out: dict[str, dict] = {}
    for table_name in {c: True for c in codes}:  # de-dupe preserves order
        table = Base.metadata.tables.get(table_name)
        if table is None:
            continue
        rows = await db.execute(select(table))
        # Some content tables are keyed by `value` per number; we return all
        for r in rows.mappings().all():
            out.setdefault(table_name, []).append(dict(r))
    return out


# ---------------------------------------------------------------------------
# Refund — reverse a paid order (minimal; no formal state machine)
# ---------------------------------------------------------------------------


async def refund_order(
    db: AsyncSession,
    order_id: int,
    reason: str,
    admin_user_id: int,
) -> Order:
    """Mark order as refunded, reverse quota/report, enqueue refund email.

    Validates order.status == 'paid' — raises ValueError otherwise.
    Idempotent: if already refunded, returns order as-is (caller checks).
    """
    from app.db.models.user import User

    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items))
        .with_for_update()
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise ValueError(f"Order {order_id} not found")

    if order.status == "refunded":
        return order  # idempotent — caller surfaces "already refunded"

    if order.status != "paid":
        raise ValueError(f"Cannot refund order in status '{order.status}' (must be 'paid')")

    now = datetime.now(timezone.utc)
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    note_line = f"{timestamp_str} [{admin_user_id}] {reason}"
    existing_notes = order.admin_notes or ""
    order.admin_notes = f"{existing_notes}\n{note_line}".lstrip("\n")
    order.status = "refunded"
    order.refunded_at = now

    # Reverse fulfillment per product type
    product_ids = [it.product_id for it in order.items]
    products_q = await db.execute(select(Product).where(Product.id.in_(product_ids)))
    products = {p.id: p for p in products_q.scalars().all()}

    for it in order.items:
        product = products.get(it.product_id)
        if product is None:
            continue
        if product.type == "package":
            await _reverse_package(db, order, product, qty=it.qty)
        elif product.type in ("report", "combo"):
            await _disable_user_reports(db, order)

    await db.flush()

    # Enqueue refund email (best-effort)
    try:
        from app.services import email_outbox_service

        user_q = await db.execute(select(User).where(User.id == order.user_id))
        user = user_q.scalar_one_or_none()
        if user is not None:
            await email_outbox_service.enqueue(
                db,
                to_email=user.email,
                template="order-refund",
                payload={
                    "ref_code": order.ref_code,
                    "order_id": order.id,
                    "total_amount_vnd": f"{order.total_amount:,}".replace(",", "."),
                    "reason": reason,
                    "refunded_at": timestamp_str,
                    "frontend_url": settings.frontend_url.rstrip("/"),
                },
                user_id=user.id,
            )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to enqueue order_refund email for order %s", order.id)

    return order


async def _reverse_package(
    db: AsyncSession, order: Order, product: Product, qty: int
) -> None:
    """Decrement profile quota by the amount originally granted and expire UserPackage rows."""
    from app.db.models.package import Package as LegacyPackage, UserPackage
    from app.db.models.user import UserProfile

    quota = (product.quota or 0) * qty
    if quota > 0:
        prof_q = await db.execute(
            select(UserProfile).where(UserProfile.user_id == order.user_id)
        )
        profile = prof_q.scalar_one_or_none()
        if profile is not None:
            profile.number_download = max(0, (profile.number_download or 0) - quota)

    # Expire any matching UserPackage row(s) so dashboard shows refunded packages as inactive.
    legacy_q = await db.execute(
        select(LegacyPackage).where(LegacyPackage.name == product.name).limit(1)
    )
    legacy_pkg = legacy_q.scalar_one_or_none()
    if legacy_pkg is not None:
        ups_q = await db.execute(
            select(UserPackage).where(
                UserPackage.user_id == order.user_id,
                UserPackage.package_id == legacy_pkg.id,
                UserPackage.is_used == True,  # noqa: E712
            )
        )
        now = datetime.now(timezone.utc)
        for up in ups_q.scalars().all():
            up.is_used = False
            up.expires_at = now
    await db.flush()


async def _disable_user_reports(db: AsyncSession, order: Order) -> None:
    """Mark user_reports for this order as disabled (set pdf_path to empty sentinel)."""
    reports_q = await db.execute(
        select(UserReport).where(UserReport.order_id == order.id)
    )
    for report in reports_q.scalars().all():
        # Prefix path with 'REFUNDED/' to invalidate download without deleting row
        if not report.pdf_path.startswith("REFUNDED/"):
            report.pdf_path = f"REFUNDED/{report.pdf_path}"
    await db.flush()


# ---------------------------------------------------------------------------
# Lead-magnet entry point (called from auth.register)
# ---------------------------------------------------------------------------


async def grant_lead_magnet(
    db: AsyncSession, user_id: int, profile_name: str, birth_day: Optional[str] = None
) -> Optional[UserReport]:
    """One-time free report on signup. Idempotent per user.

    Looks up `pkg-mini-free` style product by sku=report-mini-free.
    Returns the UserReport row (or None if product not configured).
    """
    q = await db.execute(select(Product).where(Product.sku == "report-mini-free"))
    product = q.scalar_one_or_none()
    if product is None:
        logger.warning("Lead magnet product 'report-mini-free' not seeded; skipping")
        return None

    # Idempotency: at most one lead magnet per user
    existing_q = await db.execute(
        select(UserReport).where(
            UserReport.user_id == user_id, UserReport.product_id == product.id
        )
    )
    existing = existing_q.scalar_one_or_none()
    if existing is not None:
        return existing

    return await _fulfill_report(
        db,
        order=None,
        product=product,
        user_id=user_id,
    )
