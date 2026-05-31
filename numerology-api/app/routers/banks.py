"""Banks router — GET /api/banks."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.db.models.user import User
from app.db.models.package import Bank
from app.schemas.bank import BankOut

banks_router = APIRouter(prefix="/api", tags=["banks"])


@banks_router.get("/banks", response_model=dict)
async def list_banks(
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all banks. Matches Django BankList view."""
    result = await db.execute(select(Bank))
    banks = result.scalars().all()
    return {"data": [BankOut.model_validate(b).model_dump() for b in banks]}
