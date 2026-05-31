"""Admin packages router — full CRUD on Package model."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.db.models.package import Package
from app.schemas.package import PackageOut, PackageCreate, PackageUpdate
from app.utils.pagination import PageParams, paginate

router = APIRouter(tags=["admin-packages"])


@router.get("/packages")
async def list_packages(
    page: PageParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Paginated list of packages."""
    stmt = select(Package).order_by(Package.id)
    items, total = await paginate(db, stmt, page)
    return {
        "items": [PackageOut.model_validate(p).model_dump() for p in items],
        "total": total,
        "limit": page.limit,
        "offset": page.offset,
    }


@router.get("/packages/{package_id}")
async def get_package(package_id: int, db: AsyncSession = Depends(get_db)):
    """Get single package by id or 404."""
    result = await db.execute(select(Package).where(Package.id == package_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")
    return PackageOut.model_validate(item).model_dump()


@router.post("/packages", status_code=status.HTTP_201_CREATED)
async def create_package(body: PackageCreate, db: AsyncSession = Depends(get_db)):
    """Create a new package."""
    item = Package(**body.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return PackageOut.model_validate(item).model_dump()


@router.put("/packages/{package_id}")
async def update_package(
    package_id: int, body: PackageUpdate, db: AsyncSession = Depends(get_db)
):
    """Partial update package fields."""
    result = await db.execute(select(Package).where(Package.id == package_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    await db.flush()
    await db.refresh(item)
    return PackageOut.model_validate(item).model_dump()


@router.delete("/packages/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_package(package_id: int, db: AsyncSession = Depends(get_db)):
    """Delete package or 404."""
    result = await db.execute(select(Package).where(Package.id == package_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")
    await db.delete(item)
