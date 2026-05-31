"""Pydantic schemas for bank endpoints."""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class BankOut(BaseModel):
    """Matches Django BankSerializer."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    bank: str
    branch: Optional[str] = None
    account_number: str
    account_holder: str
    image: Optional[str] = None
    code: Optional[str] = None


class BankCreate(BaseModel):
    bank: str
    branch: Optional[str] = None
    account_number: str
    account_holder: str
    image: Optional[str] = None
    code: Optional[str] = None


class BankUpdate(BaseModel):
    bank: Optional[str] = None
    branch: Optional[str] = None
    account_number: Optional[str] = None
    account_holder: Optional[str] = None
    image: Optional[str] = None
    code: Optional[str] = None
