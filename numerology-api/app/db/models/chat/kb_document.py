"""KbDocument — a logical source unit (numerology row, PDF, news article) ingested into KB.

One document → N chunks. (source_type, source_ref) is the natural key used by
the ingestion service to identify already-seen documents and trigger reindex.
"""

from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin

# JSONB on PG (indexable, binary-stored); falls back to JSON on sqlite tests.
_JSONB_OR_JSON = JSONB().with_variant(JSON(), "sqlite")


class KbDocument(TimestampMixin, Base):
    __tablename__ = "kb_documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # e.g. "numerology:mission_number", "user_pdf", "news"
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # external natural key inside source_type — e.g. numerology code, pdf id
    source_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    doc_metadata: Mapped[dict] = mapped_column(
        "metadata", _JSONB_OR_JSON, nullable=False, default=dict, server_default="{}"
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint("source_type", "source_ref", name="uq_kb_documents_source"),
    )


__all__ = ["KbDocument"]
