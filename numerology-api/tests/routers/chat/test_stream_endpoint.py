"""Integration tests for POST /api/chat/conversations/{id}/messages/stream (SSE).

LlmService.generate_stream and RetrievalService.retrieve are monkeypatched so
the test never touches pgvector or the real Gemini API.

SSE parse helper reads the raw bytes and returns a list of (event, data) tuples.
"""

# ruff: noqa: UP017, UP035, I001
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat.quota_usage import ChatQuotaUsage
from app.schemas.chat.retrieval import RetrievedChunk
from app.services.chat.llm_service import LlmError, LlmService
from app.services.chat.prompt_cache_service import PromptCacheResult, PromptCacheService
from app.services.chat.quota_service import QuotaConflictError, QuotaService
from app.services.chat.rate_limit_service import RateLimitResult, RateLimitService
from app.services.chat.retrieval_service import RetrievalService
from app.services.chat.semantic_cache_service import CachedAnswer, SemanticCacheService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


def _parse_sse(body: bytes) -> list[tuple[str, dict]]:
    """Parse raw SSE bytes into [(event_name, data_dict), ...] list."""
    events: list[tuple[str, dict]] = []
    current_event: str | None = None
    for raw_line in body.decode("utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("event:"):
            current_event = line[len("event:"):].strip()
        elif line.startswith("data:"):
            payload = line[len("data:"):].strip()
            events.append((current_event or "message", json.loads(payload)))
            current_event = None
    return events


async def _fake_stream(*tokens: str) -> AsyncIterator[str]:
    """Async generator that yields the given tokens sequentially."""
    for tok in tokens:
        yield tok


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def patch_stream_services(monkeypatch):
    """Default happy-path: 2 chunks; stream yields 3 tokens citing [1].
    Semantic cache always misses so tests skip cache logic by default.
    """

    async def _retrieve(self, query, top_k=None, threshold=None, pdf_context_id=None):
        return [_fake_chunk(1), _fake_chunk(2, score=0.8)]

    async def _generate_stream(self, system, user_content, tier="flash", result=None, cached_content=None):  # noqa: E501
        tokens = ["Ý nghĩa ", "số 7 ", "là X [1]."]
        for tok in tokens:
            if result is not None:
                result.input_tokens = 50
                result.output_tokens = 12
                result.model_used = "gemini-2.0-flash"
            yield tok

    async def _cache_miss(self, query, tier):
        return None

    async def _cache_insert(self, query, tier, answer, citations=None):
        return 1

    monkeypatch.setattr(RetrievalService, "retrieve", _retrieve)
    monkeypatch.setattr(LlmService, "generate_stream", _generate_stream)
    monkeypatch.setattr(SemanticCacheService, "lookup", _cache_miss)
    monkeypatch.setattr(SemanticCacheService, "insert", _cache_insert)


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


class TestStreamEndpointHappyPath:
    async def test_status_200_and_content_type(
        self, client, auth_headers, patch_stream_services
    ):
        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "SSE test"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages/stream",
            json={"content": "Ý nghĩa số 7?"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")

    async def test_delta_events_emitted(
        self, client, auth_headers, patch_stream_services
    ):
        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "delta"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages/stream",
            json={"content": "số 7"},
            headers=auth_headers,
        )
        events = _parse_sse(resp.content)
        delta_events = [e for e in events if e[0] == "delta"]
        assert len(delta_events) == 3
        tokens = [e[1]["token"] for e in delta_events]
        assert "".join(tokens) == "Ý nghĩa số 7 là X [1]."

    async def test_citations_event_emitted(
        self, client, auth_headers, patch_stream_services
    ):
        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "cite"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages/stream",
            json={"content": "số 7"},
            headers=auth_headers,
        )
        events = _parse_sse(resp.content)
        cite_events = [e for e in events if e[0] == "citations"]
        assert len(cite_events) == 1
        citations = cite_events[0][1]["citations"]
        # [1] in accumulated text → maps to chunk_id=101
        assert len(citations) == 1
        assert citations[0]["chunk_id"] == 101
        assert citations[0]["index"] == 1

    async def test_done_event_emitted_with_message_id(
        self, client, auth_headers, patch_stream_services
    ):
        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "done"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages/stream",
            json={"content": "số 7"},
            headers=auth_headers,
        )
        events = _parse_sse(resp.content)
        done_events = [e for e in events if e[0] == "done"]
        assert len(done_events) == 1
        done_data = done_events[0][1]
        assert "message_id" in done_data
        assert isinstance(done_data["message_id"], int)
        assert "input_tokens" in done_data
        assert "output_tokens" in done_data
        assert "model_used" in done_data

    async def test_assistant_message_persisted_to_db(
        self, client, auth_headers, patch_stream_services
    ):
        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "persist"},
                headers=auth_headers,
            )
        ).json()["data"]

        await client.post(
            f"/api/chat/conversations/{conv['id']}/messages/stream",
            json={"content": "số 7"},
            headers=auth_headers,
        )

        listing = await client.get(
            f"/api/chat/conversations/{conv['id']}/messages",
            headers=auth_headers,
        )
        msgs = listing.json()["data"]
        roles = [m["role"] for m in msgs]
        assert "user" in roles
        assert "assistant" in roles
        asst = next(m for m in msgs if m["role"] == "assistant")
        assert "Ý nghĩa" in asst["content"]
        assert len(asst["citations"]) == 1

    async def test_event_order_is_deltas_then_citations_then_done(
        self, client, auth_headers, patch_stream_services
    ):
        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "order"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages/stream",
            json={"content": "test"},
            headers=auth_headers,
        )
        event_names = [e[0] for e in _parse_sse(resp.content)]
        # All deltas come first, then citations, then done
        assert event_names[-1] == "done"
        assert "citations" in event_names
        cite_pos = event_names.index("citations")
        done_pos = event_names.index("done")
        assert cite_pos < done_pos
        for name in event_names[:cite_pos]:
            assert name == "delta"

    async def test_utf8_vietnamese_tokens_preserved(
        self, client, auth_headers, monkeypatch
    ):
        """ensure_ascii=False: Vietnamese text must survive SSE encoding."""
        async def _retrieve(self, query, top_k=None, threshold=None, pdf_context_id=None):
            return []

        async def _stream(self, system, user_content, tier="flash", result=None, cached_content=None):  # noqa: E501
            if result is not None:
                result.model_used = "gemini-2.0-flash"
            yield "Số đường đời là "
            yield "con đường vận mệnh."

        monkeypatch.setattr(RetrievalService, "retrieve", _retrieve)
        monkeypatch.setattr(LlmService, "generate_stream", _stream)

        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "utf8"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages/stream",
            json={"content": "hỏi"},
            headers=auth_headers,
        )
        raw = resp.content.decode("utf-8")
        assert "Số đường đời là" in raw
        assert "con đường vận mệnh." in raw


# ---------------------------------------------------------------------------
# Retrieval-failure short-circuit
# ---------------------------------------------------------------------------


class TestStreamRetrievalFailure:
    async def test_retrieval_failure_emits_no_info_delta_and_done(
        self, client, auth_headers, monkeypatch
    ):
        async def _fail(self, query, top_k=None, threshold=None, pdf_context_id=None):
            raise RuntimeError("db down")

        llm_called = {"n": 0}

        async def _stream(self, system, user_content, tier="flash", result=None, cached_content=None):  # noqa: E501
            llm_called["n"] += 1
            yield "should not appear"

        monkeypatch.setattr(RetrievalService, "retrieve", _fail)
        monkeypatch.setattr(LlmService, "generate_stream", _stream)

        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "ret-fail"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages/stream",
            json={"content": "anything"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        events = _parse_sse(resp.content)
        event_names = [e[0] for e in events]
        assert "delta" in event_names
        delta_text = "".join(e[1]["token"] for e in events if e[0] == "delta")
        assert "không có đủ thông tin" in delta_text
        assert "done" in event_names
        assert llm_called["n"] == 0  # LLM not called
        assert "error" not in event_names


# ---------------------------------------------------------------------------
# LLM error mid-stream
# ---------------------------------------------------------------------------


class TestStreamLlmError:
    async def test_llm_error_emits_error_event(
        self, client, auth_headers, monkeypatch
    ):
        async def _retrieve(self, query, top_k=None, threshold=None, pdf_context_id=None):
            return [_fake_chunk(1)]

        async def _stream(self, system, user_content, tier="flash", result=None, cached_content=None):  # noqa: E501
            yield "partial token"
            raise LlmError("upstream died mid-stream")

        monkeypatch.setattr(RetrievalService, "retrieve", _retrieve)
        monkeypatch.setattr(LlmService, "generate_stream", _stream)

        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "llm-err"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages/stream",
            json={"content": "question"},
            headers=auth_headers,
        )
        assert resp.status_code == 200  # StreamingResponse already started
        events = _parse_sse(resp.content)
        error_events = [e for e in events if e[0] == "error"]
        assert len(error_events) == 1
        assert error_events[0][1]["code"] == "llm_error"
        assert "done" not in [e[0] for e in events]

    async def test_llm_error_no_broken_assistant_message(
        self, client, auth_headers, monkeypatch
    ):
        """On mid-stream error, no incomplete assistant message should be committed."""
        async def _retrieve(self, query, top_k=None, threshold=None, pdf_context_id=None):
            return [_fake_chunk(1)]

        async def _stream(self, system, user_content, tier="flash", result=None, cached_content=None):  # noqa: E501
            raise LlmError("instant failure")
            yield  # make it an async generator

        monkeypatch.setattr(RetrievalService, "retrieve", _retrieve)
        monkeypatch.setattr(LlmService, "generate_stream", _stream)

        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "no-broken-msg"},
                headers=auth_headers,
            )
        ).json()["data"]

        await client.post(
            f"/api/chat/conversations/{conv['id']}/messages/stream",
            json={"content": "question"},
            headers=auth_headers,
        )

        listing = await client.get(
            f"/api/chat/conversations/{conv['id']}/messages",
            headers=auth_headers,
        )
        msgs = listing.json()["data"]
        # Only the user message should be persisted — no assistant row
        assert all(m["role"] == "user" for m in msgs)


# ---------------------------------------------------------------------------
# Ownership / auth
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Quota integration tests (streaming path)
# ---------------------------------------------------------------------------


class TestStreamQuota:
    async def test_stream_returns_402_when_quota_exceeded(
        self, client, auth_headers, user, db_session: AsyncSession, patch_stream_services
    ):
        """Exhausted free quota → HTTP 402 before stream opens (not an SSE error event)."""
        today = datetime.now(timezone.utc).date()
        db_session.add(ChatQuotaUsage(user_id=user.id, date=today, free_used=3, paid_used=0))
        await db_session.commit()

        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "stream-quota"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages/stream",
            json={"content": "blocked"},
            headers=auth_headers,
        )
        assert resp.status_code == 402
        detail = resp.json()["detail"]
        assert detail["code"] == "quota_exceeded"

    async def test_failed_llm_does_not_decrement_quota_stream(
        self, client, auth_headers, user, db_session: AsyncSession, monkeypatch
    ):
        """Mid-stream LLM error → quota NOT decremented."""
        async def _retrieve(self, query, top_k=None, threshold=None, pdf_context_id=None):
            return [_fake_chunk(1)]

        async def _stream(self, system, user_content, tier="flash", result=None, cached_content=None):  # noqa: E501
            raise LlmError("instant failure")
            yield  # make async generator

        monkeypatch.setattr(RetrievalService, "retrieve", _retrieve)
        monkeypatch.setattr(LlmService, "generate_stream", _stream)

        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "no-decrement-stream"},
                headers=auth_headers,
            )
        ).json()["data"]

        await client.post(
            f"/api/chat/conversations/{conv['id']}/messages/stream",
            json={"content": "will fail"},
            headers=auth_headers,
        )

        # free_used should still be 0
        quota_resp = await client.get("/api/chat/quota", headers=auth_headers)
        assert quota_resp.json()["data"]["free_used_today"] == 0


    async def test_stream_emits_quota_exceeded_postcommit_when_addon_drains_mid_request(
        self, client, auth_headers, monkeypatch, patch_stream_services
    ):
        """H4: QuotaConflictError during decrement → SSE error event emitted AFTER done.

        Sequence: assistant persisted + committed, then error event fires so FE
        upsell modal can trigger for this rare race.
        """
        async def _raise_conflict(self, user_id, decision):
            raise QuotaConflictError("drained mid-stream")

        monkeypatch.setattr(QuotaService, "decrement", _raise_conflict)

        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "quota-conflict-postcommit"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages/stream",
            json={"content": "test question"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        events = _parse_sse(resp.content)
        event_names = [e[0] for e in events]

        # done must still be emitted — user got the answer
        assert "done" in event_names

        # error event with quota_exceeded_postcommit code must follow done
        error_events = [e for e in events if e[0] == "error"]
        assert len(error_events) == 1
        assert error_events[0][1]["code"] == "quota_exceeded_postcommit"

        done_pos = event_names.index("done")
        error_pos = next(i for i, e in enumerate(events) if e[0] == "error")
        assert error_pos > done_pos  # error comes after done


class TestStreamOwnership:
    async def test_other_users_conversation_returns_404(
        self, client, auth_headers, superuser_headers, patch_stream_services
    ):
        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "owner-only"},
                headers=superuser_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages/stream",
            json={"content": "intrude"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_unauthenticated_returns_401(self, client):
        resp = await client.post(
            "/api/chat/conversations/1/messages/stream",
            json={"content": "anonymous"},
        )
        assert resp.status_code == 401

    async def test_empty_content_returns_422(
        self, client, auth_headers, patch_stream_services
    ):
        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "val"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages/stream",
            json={"content": ""},
            headers=auth_headers,
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Rate limit SSE tests
# ---------------------------------------------------------------------------


class TestStreamRateLimit:
    async def test_stream_returns_429_when_rate_limited(
        self, client, auth_headers, monkeypatch, patch_stream_services
    ):
        """RateLimitService returns allowed=False → HTTP 429 before stream opens."""

        async def _limited(self, *, user_id, ip, tier):
            return RateLimitResult(allowed=False, retry_after=5.0, reason="bucket_empty")

        monkeypatch.setattr(RateLimitService, "check_and_consume", _limited)

        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "rl-stream"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages/stream",
            json={"content": "rate limited"},
            headers=auth_headers,
        )
        # Rate limit raises before StreamingResponse → normal HTTP 429
        assert resp.status_code == 429
        assert resp.headers.get("Retry-After") == "5"
        detail = resp.json()["detail"]
        assert detail["code"] == "rate_limited"
        assert detail["retry_after"] == 5


# ---------------------------------------------------------------------------
# Stream semantic cache tests
# ---------------------------------------------------------------------------


class TestStreamSemanticCache:
    async def test_stream_cache_hit_delivers_cached_answer_without_llm(
        self, client, auth_headers, monkeypatch, patch_stream_services
    ):
        """Semantic cache hit → cached answer delta emitted, LLM NOT called."""
        llm_called = {"n": 0}

        async def _lookup(self, query, tier):
            return CachedAnswer(id=1, answer="Cached stream answer.", citations=[], score=0.96)

        async def _increment_hit(self, cache_id):
            pass

        async def _stream_spy(self, system, user_content, tier="flash", result=None, cached_content=None):  # noqa: E501
            llm_called["n"] += 1
            yield "should not appear"

        monkeypatch.setattr(SemanticCacheService, "lookup", _lookup)
        monkeypatch.setattr(SemanticCacheService, "increment_hit", _increment_hit)
        monkeypatch.setattr(LlmService, "generate_stream", _stream_spy)

        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "stream-cache-hit"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages/stream",
            json={"content": "cached question"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        events = _parse_sse(resp.content)
        event_names = [e[0] for e in events]

        # Must have delta, citations, done — no error
        assert "delta" in event_names
        assert "done" in event_names
        assert "error" not in event_names
        assert llm_called["n"] == 0

        delta_text = "".join(e[1]["token"] for e in events if e[0] == "delta")
        assert "Cached stream answer." in delta_text

        done_data = next(e[1] for e in events if e[0] == "done")
        assert done_data.get("from_cache") is True

    async def test_stream_passes_cached_content_to_llm_when_handle_exists(
        self, client, auth_headers, monkeypatch, patch_stream_services
    ):
        """PromptCacheService.get_live_handle returns handle → cached_content passed to generate_stream."""  # noqa: E501
        received_cached_content = {"val": "NOT_SET"}

        async def _lookup_none(self, query, tier):
            return None  # semantic cache miss

        async def _get_live_handle(self, cache_key):
            return PromptCacheResult(gemini_cache_id="caches/stream123", handle_id=2)

        async def _stream_spy(
            self, system, user_content, tier="flash", result=None, cached_content=None
        ):
            received_cached_content["val"] = cached_content
            tokens = ["Prompt-cached ", "answer [1]."]
            for tok in tokens:
                if result is not None:
                    result.input_tokens = 20
                    result.output_tokens = 8
                    result.model_used = "gemini-2.0-flash"
                yield tok

        monkeypatch.setattr(SemanticCacheService, "lookup", _lookup_none)
        monkeypatch.setattr(PromptCacheService, "get_live_handle", _get_live_handle)
        monkeypatch.setattr(LlmService, "generate_stream", _stream_spy)

        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "prompt-cache-stream"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages/stream",
            json={"content": "prompt cached question"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        events = _parse_sse(resp.content)
        assert "done" in [e[0] for e in events]
        assert received_cached_content["val"] == "caches/stream123"

    async def test_stream_cache_hit_yields_multiple_delta_events(
        self, client, auth_headers, monkeypatch, patch_stream_services
    ):
        """H7 fix: cached answer >40 chars must yield >= 2 delta events (streaming UX)."""
        long_answer = "A" * 100  # definitely > 40 chars → at least 3 chunks of 40

        async def _lookup(self, query, tier):
            return CachedAnswer(id=2, answer=long_answer, citations=[], score=0.95)

        async def _increment_hit(self, cache_id):
            pass

        monkeypatch.setattr(SemanticCacheService, "lookup", _lookup)
        monkeypatch.setattr(SemanticCacheService, "increment_hit", _increment_hit)

        conv = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "h7-multi-delta"},
                headers=auth_headers,
            )
        ).json()["data"]

        resp = await client.post(
            f"/api/chat/conversations/{conv['id']}/messages/stream",
            json={"content": "long cached question"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        events = _parse_sse(resp.content)
        delta_events = [e for e in events if e[0] == "delta"]
        assert len(delta_events) >= 2, (
            f"Expected >= 2 delta events for cached answer, got {len(delta_events)}"
        )
        # Concatenation must equal original answer
        assert "".join(e[1]["token"] for e in delta_events) == long_answer
