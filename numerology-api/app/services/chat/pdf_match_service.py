"""SHA256 hybrid match against system-generated user_reports.

Match is **user-scoped**: a user can never match another user's report even
if hashes collide (defense in depth — SHA256 collision is negligible, but
ownership is the right authorization model).
"""

from __future__ import annotations

import hashlib
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user_report import UserReport


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PdfMatchService:
    """Look up an existing UserReport whose `file_hash` matches the upload."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_match(self, pdf_hash: str, user_id: int) -> Optional[UserReport]:
        if not pdf_hash:
            return None
        stmt = select(UserReport).where(
            UserReport.file_hash == pdf_hash,
            UserReport.user_id == user_id,
        )
        return (await self.session.execute(stmt)).scalars().first()
