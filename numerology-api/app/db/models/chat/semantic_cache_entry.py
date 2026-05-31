# ruff: noqa: UP045, UP017
"""SemanticCacheEntry — cached (query_embedding, answer, citations) per tier.

Rows are inserted after each successful LLM answer and served on cosine
similarity hit (score >= threshold). TTL is enforced via expires_at;
nightly cleanup deletes stale rows.

SQLite compatibility notes (test environment):
- JSONB falls back to JSON (via _JsonbOrJson type below).
- pgvector falls back to Text when pgvector is not installed.
- Neither affects production behaviour (Postgres always uses native types).
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# ---------------------------------------------------------------------------
# Dialect-aware JSONB: uses native JSONB on Postgres, JSON elsewhere (SQLite).
# ---------------------------------------------------------------------------

class _JsonbOrJson(JSON):
    """Renders as JSONB on PostgreSQL, JSON on everything else (e.g. SQLite)."""

    def __repr__(self) -> str:
        return "JSONB()"


@compiles(_JsonbOrJson, "postgresql")
def _compile_jsonb_pg(element, compiler, **kw):  # noqa: D401
    return "JSONB"


# ---------------------------------------------------------------------------
# Vector type: pgvector on Postgres, Text fallback on SQLite.
# ---------------------------------------------------------------------------

try:
    from pgvector.sqlalchemy import Vector as PgVector
    _VECTOR_TYPE = PgVector(768)
except ImportError:  # pragma: no cover
    _VECTOR_TYPE = Text()  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


class SemanticCacheEntry(Base):
    __tablename__ = "semantic_cache"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tier: Mapped[str] = mapped_column(String(20), nullable=False, index=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    # query_embedding: pgvector(768) on Postgres; Text literal in SQLite test env
    query_embedding: Mapped[object] = mapped_column(_VECTOR_TYPE, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    # citations: JSONB on Postgres, JSON on SQLite
    citations: Mapped[object] = mapped_column(
        _JsonbOrJson(),
        nullable=False,
        default=list,
        server_default="[]",
    )
    hit_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_hit_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


__all__ = ["SemanticCacheEntry"]
