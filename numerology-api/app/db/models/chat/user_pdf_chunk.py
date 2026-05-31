"""UserPdfChunk — embedded slice of a parsed user-uploaded PDF.

Mirrors KbChunk but scoped to one UserPdfIndex (per-user, TTL'd). HNSW cosine
index on `embedding` is created in alembic 0011.
"""

from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

EMBEDDING_DIM = 768  # matches text-embedding-004 / KbChunk


class UserPdfChunk(Base):
    __tablename__ = "user_pdf_chunks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pdf_index_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user_pdf_index.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


__all__ = ["UserPdfChunk", "EMBEDDING_DIM"]
