"""KbChunk — a 500-token slice of a KB document with a 768-dim Gemini embedding.

Vector column uses pgvector; HNSW index is created in the Alembic migration
(SQLAlchemy DDL for HNSW with index opts is awkward, so we emit raw SQL).
"""

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, ForeignKey, Integer, JSON, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

EMBEDDING_DIM = 768  # text-embedding-004 output
_JSONB_OR_JSON = JSONB().with_variant(JSON(), "sqlite")


class KbChunk(Base):
    __tablename__ = "kb_chunks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("kb_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_metadata: Mapped[dict] = mapped_column(
        "metadata", _JSONB_OR_JSON, nullable=False, default=dict, server_default="{}"
    )


__all__ = ["KbChunk", "EMBEDDING_DIM"]
