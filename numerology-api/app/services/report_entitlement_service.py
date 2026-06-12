"""Resolve which /ket-qua report sections a viewer is entitled to see.

Tier model (v1, intentionally coarse — KISS/YAGNI):
  * Anonymous or no matching purchase  -> "free": only FREE_SECTIONS unlocked.
  * Authenticated user with a *paid* report/combo order whose input identity
    (name + birth_day) matches the report being viewed -> "paid": ALL unlocked.

Per-content-code granularity (unlock individual sections by product.content_codes)
is deliberately NOT implemented yet: the report-type products are distinct
reports (mini/overview/love/career), not à-la-carte unlocks of the summary
screen. Revisit if a product is introduced that unlocks summary sections piecemeal.

Pure-ish: one DB read (paid orders + items + product). No content is returned —
only the set of section keys, so locked content never leaves the server.
"""

from __future__ import annotations

import unicodedata
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.order import Order, OrderItem
from app.db.models.package import UserPackage
from app.db.models.user import User, UserProfile
from app.db.models.user_report import UserReport

# --- Section vocabulary (must match keys used by numerology_report_builder) ---
ALL_SECTIONS: frozenset[str] = frozenset(
    {
        "so_chu_dao",        # hero main content
        "so_chu_dao_extra",  # content_2..5 facets
        "su_menh",
        "linh_hon",
        "nhan_cach",
        "thai_do",
        "truong_thanh",
        "ngay_sinh",
        "noi_cam",
        "peaks",
        "challenges",
        "personal",
        "karmic",
        "missing",
        "name_chart",
        "power_chart",
    }
)

# Free viewers see the hero main interpretation + power chart + personal cycle.
# Everything else is a locked teaser that drives the upsell.
FREE_SECTIONS: frozenset[str] = frozenset({"so_chu_dao", "personal", "power_chart"})

_UNLOCKABLE_TYPES = {"report", "combo"}


def _strip_accents(text: str) -> str:
    """Vietnamese-aware accent + case fold for identity matching."""
    text = text.replace("đ", "d").replace("Đ", "D")
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize_name(name: str) -> str:
    """Lowercase, de-accent, collapse internal whitespace, trim."""
    return " ".join(_strip_accents(name).lower().split())


def normalize_birth_day(value: object) -> str:
    """Keep digits only (e.g. '01/02/2000' or '01022000' -> '01022000')."""
    return "".join(c for c in str(value or "") if c.isdigit())


def _identity_from_meta(meta: object) -> Optional[tuple[str, str]]:
    """Extract (normalized_name, normalized_birth_day) from order.meta payload."""
    if not isinstance(meta, dict):
        return None
    raw_name = meta.get("name") or meta.get("full_name") or ""
    raw_bd = meta.get("birth_day") or meta.get("birthday") or ""
    name = normalize_name(str(raw_name))
    birth_day = normalize_birth_day(raw_bd)
    if not name or not birth_day:
        return None
    return name, birth_day


async def is_premium_user(db: AsyncSession, user_id: int) -> bool:
    """True when the user has premium access (unlocks full content for any lookup).

    Premium = an active package subscription (UserPackage is_used + not expired,
    mirrors my_account.list_my_packages) OR remaining download quota
    (UserProfile.number_download > 0). The quota check also covers legacy/edge data
    where the package row may be absent but the user clearly paid (has downloads).
    PDF downloads are separately gated by the quota endpoint.
    """
    now = datetime.now(timezone.utc)
    pkg = await db.execute(
        select(UserPackage.id)
        .where(
            UserPackage.user_id == user_id,
            UserPackage.is_used.is_(True),
            or_(UserPackage.expires_at.is_(None), UserPackage.expires_at > now),
        )
        .limit(1)
    )
    if pkg.first() is not None:
        return True

    quota = await db.execute(
        select(UserProfile.number_download)
        .where(UserProfile.user_id == user_id, UserProfile.number_download > 0)
        .limit(1)
    )
    return quota.first() is not None


async def resolve_entitlement(
    db: AsyncSession,
    user: Optional[User],
    full_name: str,
    birth_day: str,
) -> tuple[str, frozenset[str], Optional[int], str]:
    """Return (tier, unlocked_sections, matched_order_id, pdf_source).

    tier: "free" | "paid". pdf_source picks the download path on /ket-qua:
      * "free"  → public reduced PDF (/api/so-hoc-free)
      * "quota" → premium subscriber, full PDF via the quota endpoint (/api/so-hoc)
      * "order" → per-report purchase, the fulfilled UserReport (matched_order_id)

    A logged-in user is "paid" when EITHER they hold an active premium package
    (any lookup) OR they own a paid report/combo order whose identity matches.
    """
    if user is None:
        return "free", FREE_SECTIONS, None, "free"

    # Premium (active package or remaining quota) unlocks everything for any lookup.
    if await is_premium_user(db, user.id):
        return "paid", ALL_SECTIONS, None, "quota"

    target = (normalize_name(full_name), normalize_birth_day(birth_day))
    if not target[0] or not target[1]:
        return "free", FREE_SECTIONS, None, "free"

    result = await db.execute(
        select(Order)
        .where(Order.user_id == user.id, Order.status == "paid")
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .order_by(Order.paid_at.desc().nullslast())
    )
    for order in result.scalars().all():
        # Identity must match first (cheap) before we trust this order.
        if _identity_from_meta(order.meta) != target:
            continue
        if any(
            getattr(it, "product", None) is not None
            and it.product.type in _UNLOCKABLE_TYPES
            for it in order.items
        ):
            return "paid", ALL_SECTIONS, order.id, "order"

    return "free", FREE_SECTIONS, None, "free"


async def find_order_report_download_id(
    db: AsyncSession, order_id: int
) -> Optional[int]:
    """Latest non-refunded UserReport id for an order → the PDF download target.

    The /ket-qua paid CTA links to GET /api/my/reports/{id}/download. Returns None
    when the order produced no report yet (e.g. a package-only purchase).
    """
    result = await db.execute(
        select(UserReport.id, UserReport.pdf_path)
        .where(UserReport.order_id == order_id)
        .order_by(UserReport.generated_at.desc())
    )
    for report_id, pdf_path in result.all():
        if not str(pdf_path).startswith("REFUNDED/"):
            return report_id
    return None
