"""News router — public list/detail + superuser CRUD."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_superuser, get_db
from app.db.models.news import News
from app.db.models.user import User
from app.schemas.news import NewsListOut, NewsOut, NewsCreate, NewsUpdate
from app.utils.pagination import PageParams, paginate

news_router = APIRouter(prefix="/api", tags=["news"])


@news_router.get("/news-top", response_model=dict)
async def news_top(db: AsyncSession = Depends(get_db)):
    """Top 10 news category=1 ordered by -created_at. Matches Django NewsTop."""
    stmt = select(News).where(News.category == 1).order_by(News.created_at.desc()).limit(10)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return {"data": [NewsListOut.model_validate(n).model_dump() for n in items]}


@news_router.get("/num-top", response_model=dict)
async def num_top(db: AsyncSession = Depends(get_db)):
    """All news category=2 ordered by created_at ASC. Matches Django NumTop."""
    stmt = select(News).where(News.category == 2).order_by(News.created_at.asc())
    result = await db.execute(stmt)
    items = result.scalars().all()
    return {"data": [NewsListOut.model_validate(n).model_dump() for n in items]}


@news_router.get("/news", response_model=dict)
async def list_news(page: PageParams = Depends(), db: AsyncSession = Depends(get_db)):
    """Paginated news list ordered by -created_at."""
    stmt = select(News).order_by(News.created_at.desc())
    items, total = await paginate(db, stmt, page)
    return {
        "data": [NewsListOut.model_validate(n).model_dump() for n in items],
        "total": total,
        "limit": page.limit,
        "offset": page.offset,
    }


@news_router.get("/news/{news_id}", response_model=dict)
async def get_news(news_id: int, db: AsyncSession = Depends(get_db)):
    """News detail or 404."""
    result = await db.execute(select(News).where(News.id == news_id))
    news = result.scalar_one_or_none()
    if news is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News not found")
    return {"data": NewsOut.model_validate(news).model_dump()}


@news_router.post("/news", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_news(
    body: NewsCreate,
    _: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Create news (superuser only)."""
    news = News(**body.model_dump())
    db.add(news)
    await db.flush()
    await db.refresh(news)
    return {"data": NewsOut.model_validate(news).model_dump()}


@news_router.put("/news/{news_id}", response_model=dict)
async def update_news(
    news_id: int,
    body: NewsUpdate,
    _: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Update news (superuser only)."""
    result = await db.execute(select(News).where(News.id == news_id))
    news = result.scalar_one_or_none()
    if news is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(news, field, value)
    await db.flush()
    await db.refresh(news)
    return {"data": NewsOut.model_validate(news).model_dump()}


@news_router.delete("/news/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news(
    news_id: int,
    _: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Delete news (superuser only)."""
    result = await db.execute(select(News).where(News.id == news_id))
    news = result.scalar_one_or_none()
    if news is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News not found")
    await db.delete(news)
