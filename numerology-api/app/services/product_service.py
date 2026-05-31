"""Product catalogue queries: list, get-by-slug, admin CRUD."""

from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


async def list_active(
    db: AsyncSession, type_: Optional[str] = None
) -> Sequence[Product]:
    """Public catalogue listing; optionally filter by product type."""
    stmt = select(Product).where(Product.is_active.is_(True))
    if type_:
        stmt = stmt.where(Product.type == type_)
    stmt = stmt.order_by(Product.sort_order, Product.id)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_by_slug(db: AsyncSession, slug: str) -> Optional[Product]:
    """Lookup a single product by URL slug (active or not)."""
    result = await db.execute(select(Product).where(Product.slug == slug))
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, product_id: int) -> Optional[Product]:
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def get_by_sku(db: AsyncSession, sku: str) -> Optional[Product]:
    result = await db.execute(select(Product).where(Product.sku == sku))
    return result.scalar_one_or_none()


async def create_product(db: AsyncSession, body: ProductCreate) -> Product:
    item = Product(**body.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


async def update_product(
    db: AsyncSession, product: Product, body: ProductUpdate
) -> Product:
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(product, field, value)
    await db.flush()
    await db.refresh(product)
    return product


async def delete_product(db: AsyncSession, product: Product) -> None:
    await db.delete(product)
