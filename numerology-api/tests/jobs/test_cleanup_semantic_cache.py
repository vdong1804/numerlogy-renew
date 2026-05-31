# ruff: noqa: UP017, UP045, I001
"""Tests for app/jobs/cleanup_semantic_cache.py.

Uses in-memory SQLite via a patched async_session_factory — no real DB needed.
Semantic cache and prompt cache tables are created by Base.metadata.create_all
(driven by conftest engine fixture).
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.chat.prompt_cache_service import PromptCacheService
from app.services.chat.semantic_cache_service import SemanticCacheService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _count_rows(db: AsyncSession, table: str) -> int:
    result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))  # noqa: S608
    return result.scalar_one()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCleanupSemanticCache:
    async def test_cleanup_returns_counts_for_both_caches(
        self, db_session: AsyncSession, monkeypatch
    ):
        """run() returns dict with semantic_cache and prompt_cache_handles keys."""
        import app.jobs.cleanup_semantic_cache as job_module
        from unittest.mock import AsyncMock, MagicMock

        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=db_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        monkeypatch.setattr(
            "app.jobs.cleanup_semantic_cache.async_session_factory",
            lambda: mock_ctx,
        )

        async def _sem_cleanup(self):
            return 3

        async def _pc_cleanup(self):
            return 1

        monkeypatch.setattr(SemanticCacheService, "cleanup_expired", _sem_cleanup)
        monkeypatch.setattr(PromptCacheService, "cleanup_expired", _pc_cleanup)

        result = await job_module.run()
        assert result == {"semantic_cache": 3, "prompt_cache_handles": 1}

    async def test_cleanup_handles_empty_tables(
        self, db_session: AsyncSession, monkeypatch
    ):
        """run() returns zeros when tables are empty."""
        import app.jobs.cleanup_semantic_cache as job_module
        from unittest.mock import AsyncMock, MagicMock

        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=db_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        monkeypatch.setattr(
            "app.jobs.cleanup_semantic_cache.async_session_factory",
            lambda: mock_ctx,
        )

        async def _sem_cleanup_zero(self):
            return 0

        async def _pc_cleanup_zero(self):
            return 0

        monkeypatch.setattr(SemanticCacheService, "cleanup_expired", _sem_cleanup_zero)
        monkeypatch.setattr(PromptCacheService, "cleanup_expired", _pc_cleanup_zero)

        result = await job_module.run()
        assert result["semantic_cache"] == 0
        assert result["prompt_cache_handles"] == 0

    async def test_cleanup_deletes_only_expired_rows(
        self, db_session: AsyncSession, monkeypatch
    ):
        """cleanup_expired on SemanticCacheService returns correct deleted count."""
        from datetime import datetime, timedelta
        from sqlalchemy import text as sqla_text
        from app.services.chat.embedding_service import EmbeddingService

        async def _embed_one(self, text):
            return [0.0] * 768

        monkeypatch.setattr(EmbeddingService, "embed_one", _embed_one)

        svc = SemanticCacheService(db_session, EmbeddingService())

        # Insert 2 expired + 1 live row directly
        past_str = (datetime.utcnow() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        future_str = (datetime.utcnow() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        dummy_vec = "[" + ",".join(["0.0"] * 768) + "]"

        for expires in [past_str, past_str, future_str]:
            await db_session.execute(
                sqla_text(
                    "INSERT INTO semantic_cache "
                    "(tier, query_text, query_embedding, answer, citations, expires_at) "
                    "VALUES (:tier, :qt, CAST(:emb AS vector), :ans, CAST(:cit AS jsonb), :exp)"
                ),
                {
                    "tier": "flash",
                    "qt": "q",
                    "emb": dummy_vec,
                    "ans": "a",
                    "cit": "[]",
                    "exp": expires,
                },
            )
        await db_session.flush()

        deleted = await svc.cleanup_expired()
        assert deleted == 2

    async def test_cleanup_commit_called(
        self, db_session: AsyncSession, monkeypatch
    ):
        """run() commits the session after cleanup."""
        import app.jobs.cleanup_semantic_cache as job_module
        from unittest.mock import AsyncMock, MagicMock

        commit_called = {"n": 0}

        class _FakeSession:
            async def commit(self):
                commit_called["n"] += 1

        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=_FakeSession())
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        monkeypatch.setattr(
            "app.jobs.cleanup_semantic_cache.async_session_factory",
            lambda: mock_ctx,
        )

        async def _sem(self):
            return 0

        async def _pc(self):
            return 0

        monkeypatch.setattr(SemanticCacheService, "cleanup_expired", _sem)
        monkeypatch.setattr(PromptCacheService, "cleanup_expired", _pc)

        await job_module.run()
        assert commit_called["n"] == 1

    async def test_cleanup_result_shape(
        self, db_session: AsyncSession, monkeypatch
    ):
        """run() always returns dict with both keys regardless of counts."""
        import app.jobs.cleanup_semantic_cache as job_module
        from unittest.mock import AsyncMock, MagicMock

        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=db_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        monkeypatch.setattr(
            "app.jobs.cleanup_semantic_cache.async_session_factory",
            lambda: mock_ctx,
        )

        async def _sem(self):
            return 10

        async def _pc(self):
            return 5

        monkeypatch.setattr(SemanticCacheService, "cleanup_expired", _sem)
        monkeypatch.setattr(PromptCacheService, "cleanup_expired", _pc)

        result = await job_module.run()
        assert set(result.keys()) == {"semantic_cache", "prompt_cache_handles"}
        assert result["semantic_cache"] == 10
        assert result["prompt_cache_handles"] == 5
