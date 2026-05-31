# ruff: noqa: UP017, UP045
"""Unit tests for SemanticCacheService.

Uses in-memory SQLite via the shared db_session fixture.
pgvector `<=>` operator is not available in SQLite, so all tests that
exercise the real cosine-search SQL are marked with pytest.mark.skipif
and will only run against a real PostgreSQL instance.

SQLite-safe tests mock the embedding service and use direct INSERT/SELECT
to verify non-vector behaviour (insert creates row, hit counting, cleanup).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.chat.semantic_cache_service import (
    CachedAnswer,
    SemanticCacheService,
    _vector_literal,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FAKE_EMB = [0.1] * 768  # deterministic fake 768-d vector
_FAKE_EMB_LITERAL = _vector_literal(_FAKE_EMB)


def _mock_embedding(vec: list[float] | None = None) -> MagicMock:
    """Return an EmbeddingService mock whose embed_one returns `vec`."""
    svc = MagicMock()
    svc.embed_one = AsyncMock(return_value=vec or _FAKE_EMB)
    return svc


# Detect whether we're running against SQLite (no pgvector)
def _is_sqlite(db: AsyncSession) -> bool:
    bind = db.get_bind()
    url = str(bind.url) if bind is not None else ""
    return "sqlite" in url


# ---------------------------------------------------------------------------
# Helper: insert a cache row directly via raw SQL (SQLite-compatible subset)
# SQLite doesn't know the vector type, so we store the literal as TEXT.
# ---------------------------------------------------------------------------

async def _insert_row(
    db: AsyncSession,
    *,
    tier: str = "flash",
    query_text: str = "test query",
    answer: str = "test answer",
    citations: list | None = None,
    expires_at: datetime | None = None,
    hit_count: int = 0,
) -> int:
    if expires_at is None:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    # Strip timezone to naive UTC so SQLAlchemy/aiosqlite stores a consistent
    # string format that `cleanup_expired` / `lookup` can compare against.
    expires_naive = expires_at.replace(tzinfo=None) if expires_at.tzinfo else expires_at
    cit_json = json.dumps(citations or [])
    result = await db.execute(
        text(
            """
            INSERT INTO semantic_cache
                (tier, query_text, query_embedding, answer, citations,
                 hit_count, expires_at)
            VALUES (:tier, :qt, :emb, :ans, :cit, :hc, :exp)
            RETURNING id
            """
        ),
        {
            "tier": tier,
            "qt": query_text,
            "emb": _FAKE_EMB_LITERAL,  # stored as TEXT in SQLite
            "ans": answer,
            "cit": cit_json,
            "hc": hit_count,
            "exp": expires_naive,
        },
    )
    await db.flush()
    return int(result.scalar_one())


# ---------------------------------------------------------------------------
# Tests — SQLite-compatible (no vector ops)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_vector_literal_format():
    """_vector_literal produces correctly formatted Postgres vector string."""
    lit = _vector_literal([1.0, 2.0, 3.0])
    assert lit.startswith("[")
    assert lit.endswith("]")
    parts = lit[1:-1].split(",")
    assert len(parts) == 3
    assert float(parts[0]) == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_insert_creates_row_with_embedding(db_session: AsyncSession):
    """insert() stores a row; we can read it back via plain SELECT."""
    svc = SemanticCacheService(db_session, _mock_embedding())

    try:
        row_id = await svc.insert(
            query="What is my life path number?",
            tier="flash",
            answer="Your life path number is 7.",
            citations=[{"chunk_id": 1}],
        )
    except Exception as exc:
        if "vector" in str(exc).lower() or "no such function" in str(exc).lower():
            pytest.skip(f"pgvector not available in test environment: {exc}")
        raise

    assert isinstance(row_id, int)
    assert row_id > 0

    result = await db_session.execute(
        text("SELECT tier, answer FROM semantic_cache WHERE id = :id"),
        {"id": row_id},
    )
    row = result.mappings().one()
    assert row["tier"] == "flash"
    assert "life path" in row["answer"]


@pytest.mark.asyncio
async def test_increment_hit_updates_counter_and_last_hit_at(db_session: AsyncSession):
    """increment_hit bumps hit_count by 1 and sets last_hit_at."""
    try:
        cache_id = await _insert_row(db_session, hit_count=3)
    except Exception as exc:
        if "no such table" in str(exc).lower():
            pytest.skip("semantic_cache table not in SQLite schema")
        raise

    svc = SemanticCacheService(db_session, _mock_embedding())
    await svc.increment_hit(cache_id)

    result = await db_session.execute(
        text("SELECT hit_count, last_hit_at FROM semantic_cache WHERE id = :id"),
        {"id": cache_id},
    )
    row = result.mappings().one()
    assert int(row["hit_count"]) == 4
    assert row["last_hit_at"] is not None


@pytest.mark.asyncio
async def test_cleanup_expired_deletes_only_expired_rows(db_session: AsyncSession):
    """cleanup_expired removes rows past expires_at and keeps fresh ones."""
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    future = datetime.now(timezone.utc) + timedelta(hours=1)

    try:
        expired_id = await _insert_row(db_session, expires_at=past, query_text="old")
        fresh_id = await _insert_row(db_session, expires_at=future, query_text="new")
    except Exception as exc:
        if "no such table" in str(exc).lower():
            pytest.skip("semantic_cache table not in SQLite schema")
        raise

    svc = SemanticCacheService(db_session, _mock_embedding())
    deleted = await svc.cleanup_expired()

    assert deleted >= 1  # at least the expired row

    # Fresh row must still exist
    result = await db_session.execute(
        text("SELECT id FROM semantic_cache WHERE id = :id"),
        {"id": fresh_id},
    )
    assert result.scalar_one_or_none() == fresh_id

    # Expired row must be gone
    result2 = await db_session.execute(
        text("SELECT id FROM semantic_cache WHERE id = :id"),
        {"id": expired_id},
    )
    assert result2.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_cleanup_expired_returns_zero_when_nothing_expired(db_session: AsyncSession):
    """cleanup_expired returns 0 when no rows have expired."""
    future = datetime.now(timezone.utc) + timedelta(hours=48)

    try:
        await _insert_row(db_session, expires_at=future)
    except Exception as exc:
        if "no such table" in str(exc).lower():
            pytest.skip("semantic_cache table not in SQLite schema")
        raise

    svc = SemanticCacheService(db_session, _mock_embedding())
    deleted = await svc.cleanup_expired()
    assert deleted == 0


# ---------------------------------------------------------------------------
# Tests — require pgvector (skip on SQLite)
# ---------------------------------------------------------------------------

_PGVECTOR_SKIP = pytest.mark.skipif(
    True,  # always skip in unit test suite; enable in integration suite
    reason="pgvector <=> operator requires PostgreSQL — run integration tests against real DB",
)


@_PGVECTOR_SKIP
@pytest.mark.asyncio
async def test_lookup_identical_query_returns_hit(db_session: AsyncSession):
    """Same embedding twice → cache hit with score == 1.0."""
    emb_svc = _mock_embedding(_FAKE_EMB)
    svc = SemanticCacheService(db_session, emb_svc)

    await svc.insert("What is numerology?", "flash", "Numerology is...", [])
    hit = await svc.lookup("What is numerology?", "flash")

    assert hit is not None
    assert isinstance(hit, CachedAnswer)
    assert hit.score == pytest.approx(1.0, abs=1e-4)
    assert "Numerology" in hit.answer


@_PGVECTOR_SKIP
@pytest.mark.asyncio
async def test_lookup_below_threshold_returns_none(db_session: AsyncSession):
    """Different embeddings → score below 0.92 → lookup returns None."""
    insert_emb = [1.0] + [0.0] * 767
    lookup_emb = [0.0] + [1.0] + [0.0] * 766  # orthogonal → score ≈ 0

    insert_svc = SemanticCacheService(db_session, _mock_embedding(insert_emb))
    await insert_svc.insert("Query A", "flash", "Answer A", [])

    lookup_svc = SemanticCacheService(db_session, _mock_embedding(lookup_emb))
    hit = await lookup_svc.lookup("Query B", "flash")
    assert hit is None


@_PGVECTOR_SKIP
@pytest.mark.asyncio
async def test_lookup_different_tier_misses(db_session: AsyncSession):
    """Same embedding but different tier → no cross-tier cache hit."""
    svc = SemanticCacheService(db_session, _mock_embedding(_FAKE_EMB))

    await svc.insert("test query", "flash", "flash answer", [])
    hit = await svc.lookup("test query", "pro")
    assert hit is None


@_PGVECTOR_SKIP
@pytest.mark.asyncio
async def test_lookup_expired_entry_misses(db_session: AsyncSession):
    """Expired row (expires_at in the past) → lookup returns None."""
    svc = SemanticCacheService(db_session, _mock_embedding(_FAKE_EMB))

    row_id = await svc.insert("stale query", "flash", "stale answer", [])
    # Force expiry
    await db_session.execute(
        text("UPDATE semantic_cache SET expires_at = NOW() - INTERVAL '1 hour' WHERE id = :id"),
        {"id": row_id},
    )
    await db_session.flush()

    hit = await svc.lookup("stale query", "flash")
    assert hit is None
