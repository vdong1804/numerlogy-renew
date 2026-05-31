"""CSV export service — generates order CSV bytes for admin download.

UTF-8 BOM prefix ensures Excel on Vietnamese Windows opens file correctly.
Returns raw bytes; caller wraps in StreamingResponse.
"""

import csv
import io
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.order import Order
from app.db.models.user import User
from app.utils.query import escape_like

logger = logging.getLogger(__name__)

# Guard against OOM: raise 400 if result set exceeds this.
# INTENTIONAL: bounded at 10k rows — all rows materialised in memory at once.
# For >10k, refactor to streaming row-by-row with `yield` + StreamingResponse generator.
EXPORT_ROW_LIMIT = 10_000

# Vietnamese column headers for Excel readability
CSV_HEADERS = [
    "order_id",
    "ref_code",
    "user_email",
    "product_names",
    "total_vnd",
    "status",
    "paid_at",
    "refunded_at",
    "created_at",
]


def _fmt_dt(dt: Optional[datetime]) -> str:
    """Format datetime to ISO-like string or empty string."""
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# Characters that trigger formula execution in Excel / LibreOffice Calc
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _safe_csv_cell(val: object) -> str:
    """Sanitise a cell value to prevent CSV formula injection.

    If the stringified value starts with a dangerous prefix character
    (=, +, -, @, TAB, CR) it is prefixed with a single-quote so
    spreadsheet applications treat it as literal text.
    """
    s = str(val) if val is not None else ""
    if s and s[0] in _FORMULA_PREFIXES:
        return "'" + s
    return s


def _build_query(
    email: Optional[str] = None,
    ref_code: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
):
    """Build the base SELECT with conditional WHERE clauses.

    Joins User for email filter; reused by both list endpoint and export.
    """
    stmt = (
        select(Order, User.email)
        .join(User, User.id == Order.user_id)
        .options(selectinload(Order.items))
        .order_by(Order.id.desc())
    )
    if email:
        # escape_like prevents wildcard injection (%/_) causing full-table scans
        stmt = stmt.where(User.email.ilike(f"%{escape_like(email)}%", escape="\\"))
    if ref_code:
        stmt = stmt.where(Order.ref_code.ilike(f"%{escape_like(ref_code)}%", escape="\\"))
    if status:
        stmt = stmt.where(Order.status == status)
    if date_from:
        stmt = stmt.where(Order.created_at >= date_from)
    if date_to:
        stmt = stmt.where(Order.created_at <= date_to)
    return stmt


async def export_orders_csv(
    db: AsyncSession,
    email: Optional[str] = None,
    ref_code: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> bytes:
    """Fetch filtered orders and serialise to CSV bytes with UTF-8 BOM.

    Raises:
        ValueError: if result count exceeds EXPORT_ROW_LIMIT.
    """
    stmt = _build_query(
        email=email,
        ref_code=ref_code,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )

    rows = (await db.execute(stmt)).all()

    if len(rows) > EXPORT_ROW_LIMIT:
        logger.warning(
            "CSV export blocked: result count %d exceeds limit %d",
            len(rows),
            EXPORT_ROW_LIMIT,
        )
        raise ValueError(
            f"Export would return {len(rows)} rows, exceeding the {EXPORT_ROW_LIMIT} row limit. "
            "Please narrow the date range or apply additional filters."
        )

    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(CSV_HEADERS)

    for order, user_email in rows:
        # Semicolon-separated product names (compatible with Excel VN locale)
        product_names = ";".join(item.snapshot_name for item in order.items)

        writer.writerow([
            _safe_csv_cell(order.id),
            _safe_csv_cell(order.ref_code),
            _safe_csv_cell(user_email),
            _safe_csv_cell(product_names),
            _safe_csv_cell(order.total_amount),
            _safe_csv_cell(order.status),
            _safe_csv_cell(_fmt_dt(order.paid_at)),
            _safe_csv_cell(_fmt_dt(order.refunded_at)),
            _safe_csv_cell(_fmt_dt(order.created_at)),
        ])

    # UTF-8 BOM (\xef\xbb\xbf) prepended so Excel detects encoding automatically
    return b"\xef\xbb\xbf" + buf.getvalue().encode("utf-8")


__all__ = ["export_orders_csv", "EXPORT_ROW_LIMIT", "CSV_HEADERS"]
