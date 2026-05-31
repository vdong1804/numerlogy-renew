"""Aggregations for the admin dashboard.

Light in-memory TTL cache keyed by metric name. Good enough for a few admins
hitting refresh — replace with Redis when concurrent admin count grows.
"""

import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order, OrderItem
from app.db.models.product import Product

_CACHE: dict[str, tuple[float, Any]] = {}
_TTL_SECONDS = 60


async def _cached(key: str, getter: Callable):
    now = time.time()
    entry = _CACHE.get(key)
    if entry and now - entry[0] < _TTL_SECONDS:
        return entry[1]
    value = await getter()
    _CACHE[key] = (now, value)
    return value


def invalidate_cache(key: Optional[str] = None) -> None:
    if key is None:
        _CACHE.clear()
    else:
        _CACHE.pop(key, None)


async def get_revenue_since(db: AsyncSession, since: datetime) -> int:
    stmt = select(func.coalesce(func.sum(Order.total_amount), 0)).where(
        Order.status == "paid", Order.paid_at >= since
    )
    result = await db.execute(stmt)
    return int(result.scalar_one() or 0)


async def get_kpi_summary(db: AsyncSession) -> dict:
    """Cards on top of dashboard: revenue today / week / month + counts."""
    async def _q():
        now = datetime.now(timezone.utc)
        today = datetime.combine(now.date(), datetime.min.time(), tzinfo=timezone.utc)
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        rev_today = await get_revenue_since(db, today)
        rev_week = await get_revenue_since(db, week_start)
        rev_month = await get_revenue_since(db, month_start)

        pending = (
            await db.execute(
                select(func.count(Order.id)).where(Order.status == "pending")
            )
        ).scalar_one()
        paid_count = (
            await db.execute(
                select(func.count(Order.id)).where(Order.status == "paid")
            )
        ).scalar_one()
        return {
            "revenue_today": rev_today,
            "revenue_week": rev_week,
            "revenue_month": rev_month,
            "pending_orders": int(pending or 0),
            "paid_orders": int(paid_count or 0),
        }

    return await _cached("kpi_summary", _q)


async def get_revenue_chart_30d(db: AsyncSession) -> list[dict]:
    """30-day series: ``[{"date": YYYY-MM-DD, "revenue": int}, ...]``."""

    async def _q():
        since = datetime.now(timezone.utc) - timedelta(days=30)
        stmt = (
            select(
                func.date(Order.paid_at).label("day"),
                func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
            )
            .where(Order.status == "paid", Order.paid_at >= since)
            .group_by(func.date(Order.paid_at))
            .order_by(func.date(Order.paid_at))
        )
        rows = (await db.execute(stmt)).all()
        return [
            {
                "date": (r.day.isoformat() if isinstance(r.day, date) else str(r.day)),
                "revenue": int(r.revenue or 0),
            }
            for r in rows
        ]

    return await _cached("revenue_chart_30d", _q)


async def get_top_products(db: AsyncSession, limit: int = 5) -> list[dict]:
    async def _q():
        stmt = (
            select(
                Product.id,
                Product.name,
                Product.sku,
                func.sum(OrderItem.unit_price * OrderItem.qty).label("revenue"),
                func.sum(OrderItem.qty).label("qty"),
            )
            .join(OrderItem, OrderItem.product_id == Product.id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.status == "paid")
            .group_by(Product.id)
            .order_by(func.sum(OrderItem.unit_price * OrderItem.qty).desc())
            .limit(limit)
        )
        rows = (await db.execute(stmt)).all()
        return [
            {
                "product_id": r.id,
                "name": r.name,
                "sku": r.sku,
                "revenue": int(r.revenue or 0),
                "qty": int(r.qty or 0),
            }
            for r in rows
        ]

    return await _cached(f"top_products_{limit}", _q)
