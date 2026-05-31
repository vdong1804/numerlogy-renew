"""Pagination utilities — PageParams query model + paginate() helper."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class PageParams(BaseModel):
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


async def paginate(db: AsyncSession, stmt, page: PageParams) -> tuple[list, int]:
    """Execute paginated query. Returns (items, total)."""
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()
    items = (await db.execute(stmt.limit(page.limit).offset(page.offset))).scalars().all()
    return list(items), total
