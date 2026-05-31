"""Pydantic schemas for order + checkout endpoints."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, conint

OrderStatus = Literal["pending", "paid", "cancelled", "expired", "failed", "refunded"]


class OrderItemInput(BaseModel):
    """Single line on order-create request."""

    product_id: int
    qty: conint(ge=1, le=10) = 1  # anti-abuse cap


class OrderCreateRequest(BaseModel):
    """POST /api/orders body."""

    items: list[OrderItemInput] = Field(..., min_length=1)
    # Free-form metadata: name, birthday, phone, gender for reports
    input_payload: dict = Field(default_factory=dict)


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    qty: int
    unit_price: int
    snapshot_name: str


class OrderOut(BaseModel):
    """Full order detail returned after create + status polling."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    ref_code: str
    total_amount: int
    currency: str
    status: OrderStatus
    payment_method: str
    expires_at: datetime
    paid_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    admin_notes: Optional[str] = None
    items: list[OrderItemOut] = Field(default_factory=list)
    meta: dict = Field(default_factory=dict)
    created_at: datetime


class OrderStatusOut(BaseModel):
    """Lightweight polling response."""

    id: int
    ref_code: str
    status: OrderStatus
    paid_at: Optional[datetime] = None
