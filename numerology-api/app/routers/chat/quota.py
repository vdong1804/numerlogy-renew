"""GET /api/chat/quota — current quota state for the authenticated user.

Returns QuotaOut: free balance + addon balance + can_send + decision_source.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.deps import get_current_user, get_db
from app.schemas.chat.addon import QuotaOut
from app.services.chat.quota_service import QuotaService

quota_router = APIRouter(prefix="/api/chat/quota", tags=["chat"])


@quota_router.get("", response_model=dict)
async def get_quota(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the current quota state for the authenticated user.

    Calls check() for can_send + decision_source, get_balance() for numeric
    breakdown. Both are read-only; combined into a single QuotaOut response.
    """
    svc = QuotaService(db)
    decision = await svc.check(user.id)
    balance = await svc.get_balance(user.id)

    out = QuotaOut(
        free_used_today=balance.free_used_today,
        free_limit=balance.free_limit,
        addon_remaining=balance.addon_remaining,
        addon_tier=balance.addon_tier,
        addon_expires_at=balance.addon_expires_at,
        can_send=decision.can_send,
        decision_source=decision.source,
    )
    return {"data": out.model_dump(mode="json")}
