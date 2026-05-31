# ruff: noqa: UP045, UP017
"""Pydantic schemas for chat add-on endpoints and quota responses."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class AddonPackageOut(BaseModel):
    """Serialised Package row where package_kind='chat_addon'."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float
    price_sale: float
    currency: str = "VND"
    message_count: Optional[int] = None
    tier: Optional[str] = None
    validity_days: Optional[int] = None
    description: Optional[str] = None  # maps to Package.content


class AddonPurchaseInitiateOut(BaseModel):
    """Response after POSTing to /{package_id}/purchase (pending payment created)."""

    payment_id: int
    package_id: int
    price: float
    status: int  # 1 = pending
    # Bank / QR info pulled from settings for the client to display
    bank_account_number: str
    bank_account_holder: str
    bank_code: str
    bank_name: str


class QuotaOut(BaseModel):
    """Current quota state for the authenticated user — used by GET /api/chat/quota."""

    free_used_today: int
    free_limit: int
    addon_remaining: int
    addon_tier: Optional[str] = None
    addon_expires_at: Optional[datetime] = None
    # Derived from QuotaDecision
    can_send: bool
    decision_source: Optional[Literal["addon", "free"]] = None
