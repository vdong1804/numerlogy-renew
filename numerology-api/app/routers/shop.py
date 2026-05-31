"""Public catalogue — GET /api/shop/products, /api/shop/products/{slug}.

No auth required to browse; auth is enforced when creating an order.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.schemas.product import ProductOut
from app.services import product_service

shop_router = APIRouter(prefix="/api/shop", tags=["shop"])


@shop_router.get("/products", response_model=dict)
async def list_products(
    type: Optional[str] = Query(None, description="Filter: package | report | combo"),
    db: AsyncSession = Depends(get_db),
):
    """Public catalogue listing (only is_active=true)."""
    if type and type not in ("package", "report", "combo"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="type must be one of: package, report, combo",
        )
    items = await product_service.list_active(db, type_=type)
    return {"data": [ProductOut.model_validate(p).model_dump() for p in items]}


@shop_router.get("/products/{slug}", response_model=ProductOut)
async def get_product(slug: str, db: AsyncSession = Depends(get_db)):
    """Public product detail by slug."""
    product = await product_service.get_by_slug(db, slug)
    if product is None or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return ProductOut.model_validate(product)
