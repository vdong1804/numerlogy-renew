"""Admin generic CRUD for all 22 numerology content tables."""

from typing import Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.db.models.numerology_content import (
    MainNumber, MissionNumber, SoulsNumber, DevelopmentNumber,
    LifePeak, ChallengeLife, BirthdayChart, NameChart, StagesOfLife, AttitudeNumber,
    BirthdayNumber, MatureNumber, IntrospectiveNumber, KarmicNumber, DeficitNumber,
    PhoneNumber, PersonalMonthNumber, Identifiable, MissNumber,
    PersonalYearNumber, KarmicDebtNumber, GrowthNumber, PhoneMasterDataModel,
)
from app.schemas.content import (
    NumerologyContentOut, NumerologyContentCreate, NumerologyContentUpdate,
    MainNumberOut, MainNumberCreate, MainNumberUpdate,
    PhoneMasterDataOut, PhoneMasterDataCreate, PhoneMasterDataUpdate,
)
from app.utils.pagination import PageParams, paginate

router = APIRouter(tags=["admin-content"])

# Registry: URL slug → SQLAlchemy model class
CONTENT_REGISTRY: dict = {
    "main-number": MainNumber,
    "mission-number": MissionNumber,
    "souls-number": SoulsNumber,
    "development-number": DevelopmentNumber,
    "life-peak": LifePeak,
    "challenge-life": ChallengeLife,
    "birthday-chart": BirthdayChart,
    "name-chart": NameChart,
    "stages-of-life": StagesOfLife,
    "attitude-number": AttitudeNumber,
    "birthday-number": BirthdayNumber,
    "mature-number": MatureNumber,
    "introspective-number": IntrospectiveNumber,
    "karmic-number": KarmicNumber,
    "deficit-number": DeficitNumber,
    "phone-number": PhoneNumber,
    "personal-month-number": PersonalMonthNumber,
    "identifiable": Identifiable,
    "miss-number": MissNumber,
    "personal-year-number": PersonalYearNumber,
    "karmic-debt-number": KarmicDebtNumber,
    "growth-number": GrowthNumber,
    "phone-master-data": PhoneMasterDataModel,
}


def _get_model(resource: str):
    model = CONTENT_REGISTRY.get(resource)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource '{resource}' not found. Valid: {list(CONTENT_REGISTRY)}",
        )
    return model


def _out_schema(model):
    if model is MainNumber:
        return MainNumberOut
    if model is PhoneMasterDataModel:
        return PhoneMasterDataOut
    return NumerologyContentOut


@router.get("/content/{resource}")
async def list_content(
    resource: str,
    q: Optional[str] = Query(default=None, description="Search code or title"),
    page: PageParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Paginated list with optional search by code/title."""
    model = _get_model(resource)
    stmt = select(model)
    if q and model is not PhoneMasterDataModel:
        stmt = stmt.where(or_(model.code.ilike(f"%{q}%"), model.title.ilike(f"%{q}%")))
    elif q and model is PhoneMasterDataModel:
        stmt = stmt.where(model.code.ilike(f"%{q}%"))
    items, total = await paginate(db, stmt, page)
    out = _out_schema(model)
    return {"items": [out.model_validate(i).model_dump() for i in items], "total": total,
            "limit": page.limit, "offset": page.offset}


@router.get("/content/{resource}/{item_id}")
async def get_content(resource: str, item_id: int, db: AsyncSession = Depends(get_db)):
    """Detail by id or 404."""
    model = _get_model(resource)
    result = await db.execute(select(model).where(model.id == item_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return _out_schema(model).model_validate(item).model_dump()


@router.post("/content/{resource}", status_code=status.HTTP_201_CREATED)
async def create_content(resource: str, body: dict, db: AsyncSession = Depends(get_db)):
    """Create content item. Body validated against model fields."""
    model = _get_model(resource)
    # Determine create schema and validate
    if model is MainNumber:
        validated = MainNumberCreate(**body)
    elif model is PhoneMasterDataModel:
        validated = PhoneMasterDataCreate(**body)
    else:
        validated = NumerologyContentCreate(**body)
    item = model(**validated.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return _out_schema(model).model_validate(item).model_dump()


@router.put("/content/{resource}/{item_id}")
async def update_content(
    resource: str, item_id: int, body: dict, db: AsyncSession = Depends(get_db)
):
    """Partial update."""
    model = _get_model(resource)
    result = await db.execute(select(model).where(model.id == item_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    if model is MainNumber:
        validated = MainNumberUpdate(**body)
    elif model is PhoneMasterDataModel:
        validated = PhoneMasterDataUpdate(**body)
    else:
        validated = NumerologyContentUpdate(**body)
    for field, value in validated.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    await db.flush()
    await db.refresh(item)
    return _out_schema(model).model_validate(item).model_dump()


@router.delete("/content/{resource}/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(resource: str, item_id: int, db: AsyncSession = Depends(get_db)):
    """Delete by id or 404."""
    model = _get_model(resource)
    result = await db.execute(select(model).where(model.id == item_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    await db.delete(item)
