# ruff: noqa: UP045, UP017
"""SemanticCacheService — pgvector cosine similarity cache for chat answers.

Lookup flow:
  1. Embed the incoming query.
  2. Find the nearest unexpired row for the same tier via `<=>` (cosine distance).
  3. If 1 - distance >= threshold (0.92): return CachedAnswer, else None.

Insert flow:
  After a successful LLM response, persist embedding + answer + citations.

All vector SQL uses raw text() because SQLAlchemy ORM doesn't model `<=>` natively.
Embedding is bound as a Postgres vector literal string '[x,y,...]'.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.chat.embedding_service import EmbeddingService


def _utcnow() -> datetime:
    """Naive UTC datetime — consistent string format for SQLite + Postgres."""
    return datetime.utcnow()  # noqa: UP017

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public data class
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CachedAnswer:
    id: int
    answer: str
    citations: list
    score: float


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class SemanticCacheService:
    """Semantic answer cache backed by pgvector cosine similarity."""

    def __init__(self, db: AsyncSession, embedding: EmbeddingService) -> None:
        self._db = db
        self._embedding = embedding

    # ------------------------------------------------------------------
    # lookup
    # ------------------------------------------------------------------

    async def lookup(self, query: str, tier: str) -> Optional[CachedAnswer]:
        """Return cached answer if cosine similarity >= threshold, else None."""
        emb = await self._embedding.embed_one(query)
        emb_literal = _vector_literal(emb)
        now = _utcnow()

        sql = text(
            """
            SELECT
                id,
                answer,
                citations,
                1 - (query_embedding <=> CAST(:emb AS vector)) AS score
            FROM semantic_cache
            WHERE tier = :tier
              AND expires_at > :now
            ORDER BY query_embedding <=> CAST(:emb AS vector) ASC
            LIMIT 1
            """
        )
        result = await self._db.execute(sql, {"emb": emb_literal, "tier": tier, "now": now})
        row = result.mappings().first()
        if row is None:
            return None

        score = float(row["score"])
        if score < settings.semantic_cache_threshold:
            return None

        return CachedAnswer(
            id=int(row["id"]),
            answer=row["answer"],
            citations=row["citations"] if row["citations"] is not None else [],
            score=score,
        )

    # ------------------------------------------------------------------
    # insert
    # ------------------------------------------------------------------

    async def insert(
        self,
        query: str,
        tier: str,
        answer: str,
        citations: Optional[list] = None,
    ) -> int:
        """Embed query and store in semantic_cache. Returns new row id."""
        from datetime import timedelta

        emb = await self._embedding.embed_one(query)
        emb_literal = _vector_literal(emb)
        citations_val = citations if citations is not None else []
        expires_at = _utcnow() + timedelta(hours=settings.semantic_cache_ttl_hours)

        sql = text(
            """
            INSERT INTO semantic_cache
                (tier, query_text, query_embedding, answer, citations, expires_at)
            VALUES (
                :tier,
                :query_text,
                CAST(:emb AS vector),
                :answer,
                CAST(:citations AS jsonb),
                :expires_at
            )
            RETURNING id
            """
        )
        result = await self._db.execute(
            sql,
            {
                "tier": tier,
                "query_text": query,
                "emb": emb_literal,
                "answer": answer,
                "citations": _json_dumps(citations_val),
                "expires_at": expires_at,
            },
        )
        await self._db.flush()
        return int(result.scalar_one())

    # ------------------------------------------------------------------
    # increment_hit
    # ------------------------------------------------------------------

    async def increment_hit(self, cache_id: int) -> None:
        """Bump hit_count and refresh last_hit_at for the given cache row."""
        now = _utcnow()
        sql = text(
            """
            UPDATE semantic_cache
            SET hit_count   = hit_count + 1,
                last_hit_at = :now
            WHERE id = :id
            """
        )
        await self._db.execute(sql, {"id": cache_id, "now": now})
        await self._db.flush()

    # ------------------------------------------------------------------
    # cleanup_expired
    # ------------------------------------------------------------------

    async def cleanup_expired(self) -> int:
        """Delete all expired rows. Returns count of deleted rows."""
        # Use naive UTC so the bound value matches SQLite's stored string format.
        # On Postgres the timestamptz column handles both naive and aware values.
        now = _utcnow()
        sql = text(
            "DELETE FROM semantic_cache WHERE expires_at < :now RETURNING id"
        )
        result = await self._db.execute(sql, {"now": now})
        await self._db.flush()
        return len(result.fetchall())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _vector_literal(vec: list[float]) -> str:
    """Format float list as Postgres vector literal '[x,y,...]'."""
    return "[" + ",".join(f"{float(v):.8f}" for v in vec) + "]"


def _json_dumps(val: list) -> str:
    import json
    return json.dumps(val)
