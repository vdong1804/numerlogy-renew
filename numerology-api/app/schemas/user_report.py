"""Pydantic schemas for user-generated report endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    order_id: Optional[int] = None
    product_id: int
    pdf_path: str
    generated_at: datetime
    input_payload: dict = Field(default_factory=dict)
    download_count: int = 0
    last_downloaded_at: Optional[datetime] = None
