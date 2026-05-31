# ruff: noqa: UP045, UP017, I001
"""Pydantic schemas for package, user-package, and download endpoints."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


PackageKind = Literal["pdf_download", "chat_addon"]
AddonTier = Literal["flash", "pro"]


class PackageOut(BaseModel):
    """Matches Django PackageSerializer."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float
    price_sale: float
    number_download: int
    content: Optional[str] = None
    # Phase 05: chat add-on fields (null for pdf_download packages)
    package_kind: PackageKind = "pdf_download"
    message_count: Optional[int] = None
    tier: Optional[AddonTier] = None
    validity_days: Optional[int] = None

    @field_validator("package_kind", mode="before")
    @classmethod
    def _coerce_null_package_kind(cls, v: object) -> object:
        """Return default when DB column is NULL (raw inserts, downgrade scripts)."""
        return v if v else "pdf_download"


class UserPackageOut(BaseModel):
    """Matches Django UserPackageSerializer — embeds package + profile download count."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    package: Optional[PackageOut] = None
    number_download: int = 0


class UserDownloadOut(BaseModel):
    """Matches Django UserDownloadSerializer."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


class PackageCreate(BaseModel):
    name: str
    price: float = 0.0
    price_sale: float = 0.0
    number_download: int = 0
    content: Optional[str] = None
    # Phase 05: chat add-on fields. Admin must provide message_count + tier +
    # validity_days when package_kind="chat_addon"; left null for pdf_download.
    package_kind: PackageKind = "pdf_download"
    message_count: Optional[int] = None
    tier: Optional[AddonTier] = None
    validity_days: Optional[int] = None

    @model_validator(mode="after")
    def _validate_chat_addon_fields(self) -> "PackageCreate":
        if self.package_kind == "chat_addon":
            if self.message_count is None or self.message_count < 1:
                raise ValueError("message_count required (>=1) when package_kind='chat_addon'")
            if self.tier is None:
                raise ValueError("tier required when package_kind='chat_addon'")
            if self.validity_days is None or self.validity_days < 1:
                raise ValueError("validity_days required (>=1) when package_kind='chat_addon'")
        return self


class PackageUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    price_sale: Optional[float] = None
    number_download: Optional[int] = None
    content: Optional[str] = None
    package_kind: Optional[PackageKind] = None
    message_count: Optional[int] = None
    tier: Optional[AddonTier] = None
    validity_days: Optional[int] = None

    @model_validator(mode="after")
    def _validate_chat_addon_fields(self) -> "PackageUpdate":
        # Only validate when package_kind is explicitly set to chat_addon.
        # If package_kind is None (partial update, kind not changing), skip.
        if self.package_kind == "chat_addon":
            if self.message_count is None or self.message_count < 1:
                raise ValueError("message_count required (>=1) when package_kind='chat_addon'")
            if self.tier is None:
                raise ValueError("tier required when package_kind='chat_addon'")
            if self.validity_days is None or self.validity_days < 1:
                raise ValueError("validity_days required (>=1) when package_kind='chat_addon'")
        return self
