"""Health check endpoints — liveness + detail with downstream checks."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.deps import get_db

health_router = APIRouter(prefix="/health", tags=["health"])

logger = logging.getLogger(__name__)


@health_router.get("/detail")
async def health_detail(db: AsyncSession = Depends(get_db)):
    """Component check: db, smtp (configured?), sepay (configured?)."""
    out = {"status": "ok", "components": {}}

    try:
        await db.execute(text("SELECT 1"))
        out["components"]["db"] = "ok"
    except Exception as exc:  # noqa: BLE001
        out["components"]["db"] = f"error: {exc}"
        out["status"] = "degraded"

    out["components"]["smtp"] = "configured" if settings.smtp_host else "stub"
    out["components"]["sepay"] = "configured" if settings.sepay_api_key else "stub"
    return out
