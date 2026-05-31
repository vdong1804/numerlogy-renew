"""Admin news router — full CRUD on News model."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.db.models.news import News
from app.schemas.news import NewsOut, NewsListOut, NewsCreate, NewsUpdate
from app.utils.pagination import PageParams, paginate

router = APIRouter(tags=["admin-news"])


@router.get("/news")
async def list_news(
    page: PageParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Paginated list of news articles."""
    stmt = select(News).order_by(News.created_at.desc())
    items, total = await paginate(db, stmt, page)
    return {
        "items": [NewsListOut.model_validate(n).model_dump() for n in items],
        "total": total,
        "limit": page.limit,
        "offset": page.offset,
    }


@router.get("/news/{news_id}")
async def get_news(news_id: int, db: AsyncSession = Depends(get_db)):
    """Get single news article by id or 404."""
    result = await db.execute(select(News).where(News.id == news_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News not found")
    return NewsOut.model_validate(item).model_dump()


@router.post("/news", status_code=status.HTTP_201_CREATED)
async def create_news(body: NewsCreate, db: AsyncSession = Depends(get_db)):
    """Create a new news article."""
    item = News(**body.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return NewsOut.model_validate(item).model_dump()


@router.put("/news/{news_id}")
async def update_news(
    news_id: int, body: NewsUpdate, db: AsyncSession = Depends(get_db)
):
    """Partial update news article fields."""
    result = await db.execute(select(News).where(News.id == news_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    await db.flush()
    await db.refresh(item)
    return NewsOut.model_validate(item).model_dump()


@router.delete("/news/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news(news_id: int, db: AsyncSession = Depends(get_db)):
    """Delete news article or 404."""
    result = await db.execute(select(News).where(News.id == news_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News not found")
    await db.delete(item)
