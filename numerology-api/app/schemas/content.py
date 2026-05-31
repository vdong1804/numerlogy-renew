"""Pydantic schemas for numerology content CRUD (admin)."""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class NumerologyContentOut(BaseModel):
    """Generic out schema for all 22 content tables using NumerologyContentMixin."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    value: Optional[str] = None
    title: str
    content: str
    number_page: Optional[int] = None


class NumerologyContentCreate(BaseModel):
    code: str
    value: Optional[str] = None
    title: str
    content: str
    number_page: Optional[int] = None


class NumerologyContentUpdate(BaseModel):
    code: Optional[str] = None
    value: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    number_page: Optional[int] = None


class MainNumberOut(NumerologyContentOut):
    """MainNumber extends base with content_2..5 columns."""
    content_2: Optional[str] = None
    content_3: Optional[str] = None
    content_4: Optional[str] = None
    content_5: Optional[str] = None


class MainNumberCreate(NumerologyContentCreate):
    content_2: Optional[str] = None
    content_3: Optional[str] = None
    content_4: Optional[str] = None
    content_5: Optional[str] = None


class MainNumberUpdate(NumerologyContentUpdate):
    content_2: Optional[str] = None
    content_3: Optional[str] = None
    content_4: Optional[str] = None
    content_5: Optional[str] = None


class PhoneMasterDataOut(BaseModel):
    """PhoneMasterDataModel — only code + bow (different schema from content tables)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    bow: Optional[str] = None


class PhoneMasterDataCreate(BaseModel):
    code: str
    bow: Optional[str] = None


class PhoneMasterDataUpdate(BaseModel):
    code: Optional[str] = None
    bow: Optional[str] = None
