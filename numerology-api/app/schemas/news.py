"""Pydantic schemas for news endpoints."""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, computed_field


def _strip_tags(html: str) -> str:
    """Remove HTML tags using regex (no external deps)."""
    return re.sub(r"<[^>]+>", "", html or "")


class NewsListOut(BaseModel):
    """Matches Django NewsListSerializer — list view with computed content preview."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    short_content: Optional[str] = None
    image: Optional[str] = None
    content: str

    @computed_field
    @property
    def content_preview(self) -> str:
        stripped = _strip_tags(self.content)
        return stripped[:200] + "..." if len(stripped) >= 200 else stripped


class NewsOut(BaseModel):
    """Full news detail — matches Django NewsSerializer (all fields)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    short_content: Optional[str] = None
    content: str
    category: int
    image: Optional[str] = None
    created_at: datetime


class NewsCreate(BaseModel):
    title: str
    short_content: Optional[str] = None
    content: str
    category: int = 1
    image: Optional[str] = None


class NewsUpdate(BaseModel):
    title: Optional[str] = None
    short_content: Optional[str] = None
    content: Optional[str] = None
    category: Optional[int] = None
    image: Optional[str] = None
