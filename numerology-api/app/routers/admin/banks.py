"""Admin banks router — full CRUD on Bank model."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.db.models.package import Bank
from app.schemas.bank import BankOut, BankCreate, BankUpdate
from app.utils.pagination import PageParams, paginate

router = APIRouter(tags=["admin-banks"])


@router.get("/banks")
async def list_banks(
    page: PageParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Paginated list of banks."""
    stmt = select(Bank).order_by(Bank.id)
    items, total = await paginate(db, stmt, page)
    return {
        "items": [BankOut.model_validate(b).model_dump() for b in items],
        "total": total,
        "limit": page.limit,
        "offset": page.offset,
    }


@router.get("/banks/{bank_id}")
async def get_bank(bank_id: int, db: AsyncSession = Depends(get_db)):
    """Get single bank by id or 404."""
    result = await db.execute(select(Bank).where(Bank.id == bank_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found")
    return BankOut.model_validate(item).model_dump()


@router.post("/banks", status_code=status.HTTP_201_CREATED)
async def create_bank(body: BankCreate, db: AsyncSession = Depends(get_db)):
    """Create a new bank."""
    item = Bank(**body.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return BankOut.model_validate(item).model_dump()


@router.put("/banks/{bank_id}")
async def update_bank(
    bank_id: int, body: BankUpdate, db: AsyncSession = Depends(get_db)
):
    """Partial update bank fields."""
    result = await db.execute(select(Bank).where(Bank.id == bank_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    await db.flush()
    await db.refresh(item)
    return BankOut.model_validate(item).model_dump()


@router.delete("/banks/{bank_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bank(bank_id: int, db: AsyncSession = Depends(get_db)):
    """Delete bank or 404."""
    result = await db.execute(select(Bank).where(Bank.id == bank_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found")
    await db.delete(item)
