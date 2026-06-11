"""Unit tests for EmbeddingService — Gemini API is mocked."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.chat.embedding_service import EmbeddingError, EmbeddingService


def _mock_resp(vectors: list[list[float]]) -> SimpleNamespace:
    """Build a response object shaped like genai's EmbedContentResponse."""
    return SimpleNamespace(
        embeddings=[SimpleNamespace(values=v) for v in vectors]
    )


def _make_service(mock_client: MagicMock) -> EmbeddingService:
    svc = EmbeddingService(batch_size=2, max_retries=3)
    svc._client = mock_client
    return svc


@pytest.mark.asyncio
async def test_embed_one_returns_vector():
    client = MagicMock()
    client.models.embed_content.return_value = _mock_resp([[0.1, 0.2, 0.3]])
    svc = _make_service(client)

    v = await svc.embed_one("hello")
    assert v == [0.1, 0.2, 0.3]
    client.models.embed_content.assert_called_once()


@pytest.mark.asyncio
async def test_embed_batch_splits_into_request_windows():
    client = MagicMock()
    # batch_size=2 → 5 inputs need 3 calls
    client.models.embed_content.side_effect = [
        _mock_resp([[1.0], [2.0]]),
        _mock_resp([[3.0], [4.0]]),
        _mock_resp([[5.0]]),
    ]
    svc = _make_service(client)

    out = await svc.embed_batch(["a", "b", "c", "d", "e"])
    assert out == [[1.0], [2.0], [3.0], [4.0], [5.0]]
    assert client.models.embed_content.call_count == 3


@pytest.mark.asyncio
async def test_retry_on_transient_error_then_success(monkeypatch):
    # First failure carries HTTP status code 503 (typed path);
    # second failure uses bounded token "deadline exceeded" (substring fallback).
    err_503 = Exception("Service Unavailable")
    err_503.code = 503  # type: ignore[attr-defined]
    err_timeout = Exception("deadline exceeded for embed_content")

    client = MagicMock()
    client.models.embed_content.side_effect = [
        err_503,
        err_timeout,
        _mock_resp([[7.7]]),
    ]
    svc = _make_service(client)

    async def _no_sleep(_):
        return None
    monkeypatch.setattr("app.services.chat.embedding_service.asyncio.sleep", _no_sleep)

    v = await svc.embed_one("text")
    assert v == [7.7]
    assert client.models.embed_content.call_count == 3


@pytest.mark.asyncio
async def test_non_retryable_error_raises_immediately():
    client = MagicMock()
    client.models.embed_content.side_effect = Exception("invalid api key")
    svc = _make_service(client)

    with pytest.raises(EmbeddingError):
        await svc.embed_one("text")
    assert client.models.embed_content.call_count == 1


@pytest.mark.asyncio
async def test_exhausted_retries_raises(monkeypatch):
    # Use typed status-code path to mark it retryable
    err = Exception("Service Unavailable")
    err.code = 503  # type: ignore[attr-defined]
    client = MagicMock()
    client.models.embed_content.side_effect = err
    svc = _make_service(client)

    async def _no_sleep(_):
        return None
    monkeypatch.setattr("app.services.chat.embedding_service.asyncio.sleep", _no_sleep)

    with pytest.raises(EmbeddingError):
        await svc.embed_one("text")
    assert client.models.embed_content.call_count == 3  # max_retries=3


@pytest.mark.asyncio
async def test_empty_input_returns_empty_list():
    client = MagicMock()
    svc = _make_service(client)
    assert await svc.embed_batch([]) == []
    client.models.embed_content.assert_not_called()
