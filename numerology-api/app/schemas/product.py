"""Pydantic schemas for product (catalogue) endpoints."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

ProductType = Literal["package", "report", "combo"]


class ProductOut(BaseModel):
    """Public catalogue shape; safe to expose to non-authenticated visitors."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    type: ProductType
    name: str
    slug: str
    description: Optional[str] = None
    price: int
    currency: str = "VND"
    quota: Optional[int] = None
    renewal_days: Optional[int] = None
    template_name: Optional[str] = None
    content_codes: Optional[list[str]] = None
    is_active: bool
    sort_order: int = 0
    meta: dict = Field(default_factory=dict)


class ProductCreate(BaseModel):
    sku: str
    type: ProductType
    name: str
    slug: str
    description: Optional[str] = None
    price: int = 0
    currency: str = "VND"
    quota: Optional[int] = None
    renewal_days: Optional[int] = None
    template_name: Optional[str] = None
    content_codes: Optional[list[str]] = None
    is_active: bool = True
    sort_order: int = 0
    meta: dict = Field(default_factory=dict)


class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    type: Optional[ProductType] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    currency: Optional[str] = None
    quota: Optional[int] = None
    renewal_days: Optional[int] = None
    template_name: Optional[str] = None
    content_codes: Optional[list[str]] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    meta: Optional[dict] = None


class ProductWithCreatedAt(ProductOut):
    """Used by admin endpoints that need timestamps."""

    created_at: datetime
    updated_at: datetime
