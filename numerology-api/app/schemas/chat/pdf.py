"""PDF upload + context attachment DTOs."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PdfUploadResponse(BaseModel):
    pdf_context_id: int
    matched: bool  # True when SHA256 matched a system-generated user_reports row
    matched_report_id: Optional[int] = None
    page_count: Optional[int] = None
    chunks_created: int
    expires_at: datetime


class PdfContextPatch(BaseModel):
    # Set to null to clear the attachment. Otherwise must be a user-owned pdf_context_id.
    pdf_context_id: Optional[int] = None
