"""Admin dashboard metrics router (cached aggregations)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.services import dashboard_service

router = APIRouter(tags=["admin-dashboard"])


@router.get("/dashboard/metrics")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    return await dashboard_service.get_kpi_summary(db)


@router.get("/dashboard/revenue-chart")
async def get_revenue_chart(db: AsyncSession = Depends(get_db)):
    return {"data": await dashboard_service.get_revenue_chart_30d(db)}


@router.get("/dashboard/top-products")
async def get_top_products(limit: int = 5, db: AsyncSession = Depends(get_db)):
    return {"data": await dashboard_service.get_top_products(db, limit=limit)}


@router.post("/dashboard/refresh")
async def force_refresh():
    """Invalidates the in-memory metrics cache so the next read recomputes."""
    dashboard_service.invalidate_cache()
    return {"status": "ok"}
