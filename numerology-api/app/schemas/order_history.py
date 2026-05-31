"""Schemas for /my/* order history and report library endpoints."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class MyOrderItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    qty: int
    unit_price: int
    snapshot_name: str


class MyOrderSummary(BaseModel):
    """Light row for the orders list (no items)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ref_code: str
    total_amount: int
    currency: str
    status: str
    paid_at: Optional[datetime] = None
    expires_at: datetime
    created_at: datetime


class MyOrderDetail(MyOrderSummary):
    items: list[MyOrderItem] = Field(default_factory=list)
    meta: dict = Field(default_factory=dict)


class MyReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: Optional[int] = None
    product_id: int
    pdf_path: str
    generated_at: datetime
    input_payload: dict = Field(default_factory=dict)
    download_count: int = 0
    last_downloaded_at: Optional[datetime] = None


class MyDashboardSummary(BaseModel):
    """Aggregated stats for /my-account landing page."""

    quota_total: int = 0
    quota_used: int = 0
    quota_remaining: int = 0
    active_package_id: Optional[int] = None
    active_package_name: Optional[str] = None
    active_package_total: Optional[int] = None
    active_package_acquired_at: Optional[datetime] = None
    active_package_expires_at: Optional[datetime] = None
    orders_count: int = 0
    reports_count: int = 0
    recent_orders: list["MyOrderSummary"] = Field(default_factory=list)
    recent_reports: list["MyReportOut"] = Field(default_factory=list)


class NotificationPrefs(BaseModel):
    """Whitelist-only notification preferences (extend carefully)."""

    order_paid_email: bool = True
    quota_low_email: bool = True
    marketing_email: bool = False


class MyActivePackage(BaseModel):
    """Active subscription package summary."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    package_id: int
    name: str
    quota_total: int
    quota_remaining: int
    acquired_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True


class MyDownloadEntry(BaseModel):
    """Single download history row for /my/downloads."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    birth_day: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    type: int  # 0=free, 1=paid
    created_at: datetime


class MyProfileUpdate(BaseModel):
    """Editable profile fields under /my/profile."""

    name: Optional[str] = None
    birth_day: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class MyProfileOut(BaseModel):
    """User + profile combined output under /my/profile."""

    id: int
    email: str
    first_name: str = ""
    last_name: str = ""
    name: str = ""
    birth_day: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    number_download: int = 0
    notification_prefs: dict[str, Any] = Field(default_factory=dict)


# Resolve forward refs for MyDashboardSummary (recent_orders/recent_reports)
MyDashboardSummary.model_rebuild()
