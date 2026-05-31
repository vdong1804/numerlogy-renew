"""Admin products router — full CRUD on Product model."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.product import Product
from app.deps import get_db
from app.schemas.product import (
    ProductCreate,
    ProductOut,
    ProductUpdate,
)
from app.services import product_service
from app.utils.pagination import PageParams, paginate

router = APIRouter(tags=["admin-products"])


@router.get("/products")
async def list_products(
    type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: PageParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Paginated admin product list (sees inactive too)."""
    stmt = select(Product).order_by(Product.sort_order, Product.id)
    if type:
        stmt = stmt.where(Product.type == type)
    if is_active is not None:
        stmt = stmt.where(Product.is_active.is_(is_active))
    items, total = await paginate(db, stmt, page)
    return {
        "items": [ProductOut.model_validate(p).model_dump() for p in items],
        "total": total,
        "limit": page.limit,
        "offset": page.offset,
    }


@router.get("/products/{product_id}")
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    item = await product_service.get_by_id(db, product_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return ProductOut.model_validate(item).model_dump()


@router.post("/products", status_code=status.HTTP_201_CREATED)
async def create_product(body: ProductCreate, db: AsyncSession = Depends(get_db)):
    # Pre-check sku/slug to give friendly errors instead of raw IntegrityError
    if await product_service.get_by_sku(db, body.sku):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="SKU already exists"
        )
    if await product_service.get_by_slug(db, body.slug):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Slug already exists"
        )
    item = await product_service.create_product(db, body)
    return ProductOut.model_validate(item).model_dump()


@router.put("/products/{product_id}")
async def update_product(
    product_id: int, body: ProductUpdate, db: AsyncSession = Depends(get_db)
):
    item = await product_service.get_by_id(db, product_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    updated = await product_service.update_product(db, item, body)
    return ProductOut.model_validate(updated).model_dump()


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    item = await product_service.get_by_id(db, product_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    await product_service.delete_product(db, item)
