"""Integration tests for POST /api/chat/conversations/{id}/messages.

RetrievalService and LlmService are monkeypatched so the test never touches
pgvector or the real DeepSeek API.
"""

# ruff: noqa: UP017, I001
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat.quota_usage import ChatQuotaUsage
from app.schemas.chat.retrieval import RetrievedChunk
from app.services.chat.llm_service import LlmError, LlmResponse, LlmService
from app.services.chat.rate_limit_service import RateLimitResult, RateLimitService
from app.services.chat.retrieval_service import RetrievalService
from app.services.chat.semantic_cache_service import CachedAnswer, SemanticCacheService


def _fake_chunk(i: int, score: float = 0.9) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=100 + i,
        document_id=10 + i,
        source_type="numerology:mission_number",
        source_ref=f"MN_{i}",
        title=f"T{i}",
        content=f"Excerpt {i}",
        score=score,
    )


@pytest.fixture(autouse=True)
def _stub_semantic_cache_globally(monkeypatch):
    """Always stub SemanticCacheService.lookup to miss and insert to no-op.
    Individual tests that need cache-hit behaviour override these per-test.
    """
    async def _miss(self, query, tier):
        return None

    async def _noop_insert(self, query, tier, answer, citations=None):
        return 1

    monkeypatch.setattr(SemanticCacheService, "lookup", _miss)
    monkeypatch.setattr(SemanticCacheService, "insert", _noop_insert)


@pytest.fixture
def patch_chat_services(monkeypatch):
    """Default: retrieval returns 2 chunks; LLM returns answer citing [1].
    Semantic cache always misses (returns None) so tests skip cache logic by default.
    """

    async def _retrieve(self, query, top_k=None, threshold=None, pdf_context_id=None):
        return [_fake_chunk(1), _fake_chunk(2, 0.8)]

    async def _generate(self, system, user_content, tier="flash"):
        return LlmResponse(
            text="The meaning is X per [1].",
            model_used="gemini-2.0-flash",
            input_tokens=42,
            output_tokens=11,
        )

    async def _cache_miss(self, query, tier):
        return None

    async def _cache_insert(self, query, tier, answer, citations=None):
        return 1

    monkeypatch.setattr(RetrievalService, "retrieve", _retrieve)
    monkeypatch.setattr(LlmService, "generate", _generate)
    monkeypatch.setattr(SemanticCacheService, "lookup", _cache_miss)
    monkeypatch.setattr(SemanticCacheService, "insert", _cache_insert)


class TestSendMessage:
    async def test_send_returns_assistant_message_with_citations(
        self, client, auth_headers, patch_chat_services
    ):
        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "RAG"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages",
            json={"content": "Ý nghĩa số 7 là gì?"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["role"] == "assistant"
        assert "[1]" in data["content"]
        assert data["model_used"] == "gemini-2.0-flash"
        assert data["tier"] == "free"
        # Citation [1] resolves to chunk 101
        assert len(data["citations"]) == 1
        assert data["citations"][0]["chunk_id"] == 101

    async def test_send_persists_user_then_assistant_message(
        self, client, auth_headers, patch_chat_services
    ):
        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "history"},
                headers=auth_headers,
            )
        ).json()["data"]
        await client.post(
            f"/api/chat/conversations/{conv['id']}/messages",
            json={"content": "Hỏi 1?"},
            headers=auth_headers,
        )
        listing = await client.get(
            f"/api/chat/conversations/{conv['id']}/messages",
            headers=auth_headers,
        )
        assert listing.status_code == 200
        msgs = listing.json()["data"]
        assert [m["role"] for m in msgs] == ["user", "assistant"]
        assert msgs[0]["content"] == "Hỏi 1?"


class TestSendMessageErrors:
    async def test_unauthenticated_401(self, client):
        resp = await client.post(
            "/api/chat/conversations/1/messages",
            json={"content": "anonymous"},
        )
        assert resp.status_code == 401

    async def test_other_users_conversation_404(
        self, client, auth_headers, superuser_headers, patch_chat_services
    ):
        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "x"},
                headers=superuser_headers,
            )
        ).json()["data"]
        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages",
            json={"content": "intrude"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_empty_content_422(self, client, auth_headers, patch_chat_services):
        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "x"},
                headers=auth_headers,
            )
        ).json()["data"]
        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages",
            json={"content": ""},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_oversize_content_422(self, client, auth_headers, patch_chat_services):
        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "x"},
                headers=auth_headers,
            )
        ).json()["data"]
        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages",
            json={"content": "x" * 2001},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_retrieval_exception_returns_canonical_without_llm_call(
        self, client, auth_headers, monkeypatch
    ):
        """H8: when retrieval raises, skip LLM and return 'no info' phrase."""
        async def _retrieve_fail(self, query, top_k=None, threshold=None, pdf_context_id=None):
            raise RuntimeError("db down")

        llm_called = {"count": 0}

        async def _generate(self, system, user_content, tier="flash"):
            llm_called["count"] += 1
            return LlmResponse(text="X", model_used="m", input_tokens=1, output_tokens=1)

        monkeypatch.setattr(RetrievalService, "retrieve", _retrieve_fail)
        monkeypatch.setattr(LlmService, "generate", _generate)

        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "x"},
                headers=auth_headers,
            )
        ).json()["data"]
        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages",
            json={"content": "anything"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert "không có đủ thông tin" in data["content"]
        assert data["citations"] == []
        assert llm_called["count"] == 0  # LLM was not called

    async def test_user_message_persists_on_llm_failure(
        self, client, auth_headers, monkeypatch
    ):
        """C1: 502 from LLM must NOT lose the user's turn."""
        async def _retrieve(self, query, top_k=None, threshold=None, pdf_context_id=None):
            return []

        async def _generate(self, system, user_content, tier="flash"):
            raise LlmError("boom")

        monkeypatch.setattr(RetrievalService, "retrieve", _retrieve)
        monkeypatch.setattr(LlmService, "generate", _generate)

        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "x"},
                headers=auth_headers,
            )
        ).json()["data"]
        await client.post(
            f"/api/chat/conversations/{conv['id']}/messages",
            json={"content": "stays even on 502"},
            headers=auth_headers,
        )
        listing = await client.get(
            f"/api/chat/conversations/{conv['id']}/messages",
            headers=auth_headers,
        )
        msgs = listing.json()["data"]
        assert any(m["role"] == "user" and m["content"] == "stays even on 502" for m in msgs)

    async def test_llm_failure_returns_502(self, client, auth_headers, monkeypatch):
        async def _retrieve(self, query, top_k=None, threshold=None, pdf_context_id=None):
            return []

        async def _generate(self, system, user_content, tier="flash"):
            raise LlmError("upstream down")

        monkeypatch.setattr(RetrievalService, "retrieve", _retrieve)
        monkeypatch.setattr(LlmService, "generate", _generate)

        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "x"},
                headers=auth_headers,
            )
        ).json()["data"]
        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages",
            json={"content": "boom"},
            headers=auth_headers,
        )
        assert resp.status_code == 502


# ---------------------------------------------------------------------------
# Quota integration tests
# ---------------------------------------------------------------------------


class TestSendMessageQuota:
    async def test_send_returns_402_when_quota_exceeded(
        self, client, auth_headers, user, db_session: AsyncSession, patch_chat_services
    ):
        """User exhausted all 3 free messages today → 402 with quota_exceeded code."""
        today = datetime.now(timezone.utc).date()
        db_session.add(ChatQuotaUsage(user_id=user.id, date=today, free_used=3, paid_used=0))
        await db_session.commit()

        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "quota-test"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages",
            json={"content": "blocked message"},
            headers=auth_headers,
        )
        assert resp.status_code == 402
        detail = resp.json()["detail"]
        assert detail["code"] == "quota_exceeded"
        assert detail["upsell"] is True

    async def test_successful_send_decrements_quota(
        self, client, auth_headers, user, db_session: AsyncSession, patch_chat_services
    ):
        """Successful send → free_used incremented from 0 to 1."""
        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "decrement-test"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages",
            json={"content": "Ý nghĩa số 7?"},
            headers=auth_headers,
        )
        assert resp.status_code == 201

        # Quota endpoint reflects increment
        quota_resp = await client.get("/api/chat/quota", headers=auth_headers)
        assert quota_resp.status_code == 200
        assert quota_resp.json()["data"]["free_used_today"] == 1

    async def test_failed_llm_does_not_decrement_quota(
        self, client, auth_headers, user, db_session: AsyncSession, monkeypatch
    ):
        """LLM error → quota must NOT be decremented."""
        async def _retrieve(self, query, top_k=None, threshold=None, pdf_context_id=None):
            return []

        async def _generate(self, system, user_content, tier="flash"):
            raise LlmError("llm down")

        monkeypatch.setattr(RetrievalService, "retrieve", _retrieve)
        monkeypatch.setattr(LlmService, "generate", _generate)

        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "no-decrement"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages",
            json={"content": "will fail"},
            headers=auth_headers,
        )
        assert resp.status_code == 502


# ---------------------------------------------------------------------------
# Rate limit tests
# ---------------------------------------------------------------------------


class TestSendMessageRateLimit:
    async def test_send_returns_429_when_rate_limited(
        self, client, auth_headers, monkeypatch, patch_chat_services
    ):
        """RateLimitService returns allowed=False → 429 with Retry-After header."""

        async def _limited(self, *, user_id, ip, tier):
            return RateLimitResult(allowed=False, retry_after=7.0, reason="bucket_empty")

        monkeypatch.setattr(RateLimitService, "check_and_consume", _limited)

        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "rl-test"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages",
            json={"content": "too fast"},
            headers=auth_headers,
        )
        assert resp.status_code == 429
        assert resp.headers.get("Retry-After") == "7"
        detail = resp.json()["detail"]
        assert detail["code"] == "rate_limited"
        assert detail["retry_after"] == 7
        assert "giây" in detail["message"]


# ---------------------------------------------------------------------------
# Semantic cache tests
# ---------------------------------------------------------------------------


class TestSendMessageSemanticCache:
    async def test_send_cache_hit_skips_llm_and_returns_from_cache_true(
        self, client, auth_headers, monkeypatch, patch_chat_services
    ):
        """SemanticCacheService.lookup returns hit → LLM NOT called, from_cache=True."""
        llm_called = {"n": 0}

        _orig_generate = LlmService.generate

        async def _track_generate(self, system, user_content, tier="flash"):
            llm_called["n"] += 1
            return await _orig_generate(self, system, user_content, tier=tier)

        async def _lookup(self, query, tier):
            return CachedAnswer(id=1, answer="Cached answer [1].", citations=[], score=0.95)

        async def _increment_hit(self, cache_id):
            pass

        monkeypatch.setattr(LlmService, "generate", _track_generate)
        monkeypatch.setattr(SemanticCacheService, "lookup", _lookup)
        monkeypatch.setattr(SemanticCacheService, "increment_hit", _increment_hit)

        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "cache-hit"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages",
            json={"content": "What is 7?"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["from_cache"] is True
        assert data["model_used"] == "cache"
        assert llm_called["n"] == 0

    async def test_send_cache_hit_decrements_quota(
        self, client, auth_headers, user, db_session: AsyncSession,
        monkeypatch, patch_chat_services
    ):
        """Cache hit still decrements quota (consistent UX)."""
        async def _lookup(self, query, tier):
            return CachedAnswer(id=1, answer="Hit.", citations=[], score=0.97)

        async def _increment_hit(self, cache_id):
            pass

        monkeypatch.setattr(SemanticCacheService, "lookup", _lookup)
        monkeypatch.setattr(SemanticCacheService, "increment_hit", _increment_hit)

        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "cache-quota"},
                headers=auth_headers,
            )
        ).json()["data"]

        await client.post(
            f"/api/chat/conversations/{conv['id']}/messages",
            json={"content": "cached question"},
            headers=auth_headers,
        )
        quota_resp = await client.get("/api/chat/quota", headers=auth_headers)
        assert quota_resp.json()["data"]["free_used_today"] == 1

    async def test_send_cache_miss_inserts_into_cache_after_llm(
        self, client, auth_headers, monkeypatch, patch_chat_services
    ):
        """Cache miss → SemanticCacheService.insert called once after LLM."""
        insert_calls = {"n": 0}

        async def _lookup(self, query, tier):
            return None

        async def _insert(self, query, tier, answer, citations=None):
            insert_calls["n"] += 1
            return 1

        monkeypatch.setattr(SemanticCacheService, "lookup", _lookup)
        monkeypatch.setattr(SemanticCacheService, "insert", _insert)

        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "cache-insert"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages",
            json={"content": "new question"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert insert_calls["n"] == 1


# ---------------------------------------------------------------------------
# M4 — no-info canary response must NOT be cached
# ---------------------------------------------------------------------------


class TestSendMessageNoInfoCanary:
    async def test_send_does_not_cache_no_info_canary_response(
        self, client, auth_headers, monkeypatch
    ):
        """M4 fix: if LLM returns NO_INFO_VI canary, semantic_cache.insert must NOT be called."""
        from app.routers.chat._stream_generator import NO_INFO_VI

        insert_called = {"n": 0}

        async def _retrieve(self, query, top_k=None, threshold=None, pdf_context_id=None):
            return [_fake_chunk(1)]

        async def _generate(self, system, user_content, tier="flash"):
            return LlmResponse(
                text=NO_INFO_VI,
                model_used="gemini-2.0-flash",
                input_tokens=5,
                output_tokens=10,
            )

        async def _insert_spy(self, query, tier, answer, citations=None):
            insert_called["n"] += 1
            return 1

        async def _lookup(self, query, tier):
            return None

        monkeypatch.setattr(RetrievalService, "retrieve", _retrieve)
        monkeypatch.setattr(LlmService, "generate", _generate)
        monkeypatch.setattr(SemanticCacheService, "lookup", _lookup)
        monkeypatch.setattr(SemanticCacheService, "insert", _insert_spy)

        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "no-info-canary"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages",
            json={"content": "unknown question"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert insert_called["n"] == 0, "cache insert must not be called for no-info canary"
