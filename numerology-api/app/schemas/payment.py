"""Pydantic schemas for payment endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.package import PackageOut


class PaymentCreate(BaseModel):
    """Matches Django PaymentHistorySerializer writable fields."""
    package_id: int
    price: float
    transaction_code: str
    account_number: str
    account_holder: str
    bank: str


class PaymentOut(BaseModel):
    """Full payment record — matches Django UserPaymentSerializer."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    package: Optional[PackageOut] = None
    price: float
    transaction_code: Optional[str] = None
    account_number: Optional[str] = None
    account_holder: Optional[str] = None
    bank: Optional[str] = None
    status: int
    created_at: datetime


class PaymentStatusUpdate(BaseModel):
    status: int
