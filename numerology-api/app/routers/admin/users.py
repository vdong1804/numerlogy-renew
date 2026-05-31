"""Admin users router — list + detail with profile."""

from typing import Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import get_db
from app.db.models.user import User, UserProfile
from app.schemas.profile import UserWithProfileOut, ProfileNestedOut
from app.utils.pagination import PageParams, paginate

router = APIRouter(tags=["admin-users"])


@router.get("/users")
async def list_users(
    q: Optional[str] = Query(default=None, description="Search by email"),
    page: PageParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Paginated user list with optional email search."""
    stmt = select(User).options(selectinload(User.profile))
    if q:
        stmt = stmt.where(User.email.ilike(f"%{q}%"))
    items, total = await paginate(db, stmt, page)

    def _serialize(u: User):
        profile_data = None
        if u.profile:
            profile_data = ProfileNestedOut.model_validate(u.profile)
        return UserWithProfileOut(id=u.id, email=u.email, profile=profile_data).model_dump()

    return {"items": [_serialize(u) for u in items], "total": total,
            "limit": page.limit, "offset": page.offset}


@router.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """User detail with profile or 404."""
    result = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.profile))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    profile_data = ProfileNestedOut.model_validate(user.profile) if user.profile else None
    return UserWithProfileOut(id=user.id, email=user.email, profile=profile_data).model_dump()
