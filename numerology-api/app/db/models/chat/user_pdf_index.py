"""UserPdfIndex — one row per (user, PDF hash) pair, with 30d TTL.

Created when a user uploads a PDF to the chatbot. The `matched_report_id` FK
is populated when the hash matches a system-generated report (P3 hybrid match)
— otherwise the PDF was user-supplied and `pdf_chunks` are freshly parsed.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _default_expires_at() -> datetime:
    """Python-side default for expires_at — used on sqlite (which can't eval
    the PG `NOW() + INTERVAL '30 days'` server_default)."""
    return datetime.now(timezone.utc) + timedelta(days=30)


class UserPdfIndex(Base):
    __tablename__ = "user_pdf_index"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pdf_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    # NULL when the upload didn't match any system-generated report
    matched_report_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("user_reports.id", ondelete="SET NULL"),
        nullable=True,
    )
    filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parsed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # Default 30d TTL. Cleanup job deletes rows where expires_at < NOW().
    # PG server-side default is set in the alembic migration (NOW() + INTERVAL
    # '30 days') so raw INSERTs still get one; the Python `default=` here covers
    # ORM inserts and keeps the sqlite test DDL portable.
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_default_expires_at,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "pdf_hash", name="uq_user_pdf_index_user_hash"),
    )


__all__ = ["UserPdfIndex"]
