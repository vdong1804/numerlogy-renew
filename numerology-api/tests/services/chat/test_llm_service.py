# ruff: noqa: UP045
"""Unit tests for LlmService (DeepSeek via openai-compatible SDK).

We monkey-patch the AsyncOpenAI chat.completions.create method directly
rather than using respx, because the openai SDK wraps Server-Sent Events in a
proprietary AsyncStream object that is non-trivial to fake at the HTTP layer.
The patched-method approach mirrors how router tests stub LlmService and is
sufficient to verify our adapter logic (token wiring, error mapping,
empty-response guard).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from openai import APIConnectionError, APIError, APITimeoutError

from app.services.chat.llm_service import (
    LlmError,
    LlmResponse,
    LlmService,
    StreamResult,
)


# ---------------------------------------------------------------------------
# Fake response shapes — mirror the relevant openai SDK attributes only.
# ---------------------------------------------------------------------------


@dataclass
class _Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0


@dataclass
class _Delta:
    content: str = ""


@dataclass
class _Choice:
    delta: _Delta | None = None
    message: Any = None


@dataclass
class _Chunk:
    choices: list
    usage: _Usage | None = None


@dataclass
class _Message:
    content: str = ""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLlmServiceGenerate:
    async def test_generate_happy_path(self, monkeypatch):
        svc = LlmService(api_key="dummy")

        async def _fake_create(**kwargs):
            assert kwargs["model"] == "deepseek-chat"
            assert kwargs["messages"][0] == {"role": "system", "content": "SYS"}
            assert kwargs["messages"][1] == {"role": "user", "content": "USR"}
            assert kwargs["stream"] is False
            return _Chunk(
                choices=[_Choice(message=_Message(content="The answer is 42."))],
                usage=_Usage(prompt_tokens=11, completion_tokens=5),
            )

        monkeypatch.setattr(svc.client.chat.completions, "create", _fake_create)

        resp = await svc.generate("SYS", "USR")
        assert isinstance(resp, LlmResponse)
        assert resp.text == "The answer is 42."
        assert resp.model_used == "deepseek-chat"
        assert resp.input_tokens == 11
        assert resp.output_tokens == 5

    async def test_generate_empty_response_raises(self, monkeypatch):
        svc = LlmService(api_key="dummy")

        async def _fake_create(**kwargs):
            return _Chunk(
                choices=[_Choice(message=_Message(content=""))],
                usage=_Usage(),
            )

        monkeypatch.setattr(svc.client.chat.completions, "create", _fake_create)
        with pytest.raises(LlmError, match="empty response"):
            await svc.generate("SYS", "USR")

    async def test_generate_api_error_wraps_in_llm_error(self, monkeypatch):
        svc = LlmService(api_key="dummy")

        async def _fake_create(**kwargs):
            raise APIError("upstream broken", request=None, body=None)  # type: ignore[arg-type]

        monkeypatch.setattr(svc.client.chat.completions, "create", _fake_create)
        with pytest.raises(LlmError, match="LLM call failed"):
            await svc.generate("SYS", "USR")

    async def test_generate_timeout_wraps_in_llm_error(self, monkeypatch):
        svc = LlmService(api_key="dummy", timeout=5)

        async def _fake_create(**kwargs):
            raise APITimeoutError(request=None)  # type: ignore[arg-type]

        monkeypatch.setattr(svc.client.chat.completions, "create", _fake_create)
        with pytest.raises(LlmError, match="timed out"):
            await svc.generate("SYS", "USR")

    async def test_generate_connection_error_wraps_in_llm_error(self, monkeypatch):
        svc = LlmService(api_key="dummy")

        async def _fake_create(**kwargs):
            raise APIConnectionError(request=None)  # type: ignore[arg-type]

        monkeypatch.setattr(svc.client.chat.completions, "create", _fake_create)
        with pytest.raises(LlmError, match="LLM call failed"):
            await svc.generate("SYS", "USR")


class TestLlmServiceStream:
    async def test_stream_yields_tokens_and_populates_result(self, monkeypatch):
        svc = LlmService(api_key="dummy")

        async def _aiter():
            yield _Chunk(choices=[_Choice(delta=_Delta(content="Hello "))])
            yield _Chunk(choices=[_Choice(delta=_Delta(content="world"))])
            # Final chunk with usage (mirrors include_usage=True behavior)
            yield _Chunk(
                choices=[],
                usage=_Usage(prompt_tokens=20, completion_tokens=7),
            )

        async def _fake_create(**kwargs):
            assert kwargs["stream"] is True
            assert kwargs["stream_options"] == {"include_usage": True}
            return _aiter()

        monkeypatch.setattr(svc.client.chat.completions, "create", _fake_create)

        result = StreamResult()
        collected = []
        async for tok in svc.generate_stream("SYS", "USR", result=result):
            collected.append(tok)

        assert collected == ["Hello ", "world"]
        assert result.input_tokens == 20
        assert result.output_tokens == 7
        assert result.model_used == "deepseek-chat"

    async def test_stream_api_error_wraps_in_llm_error(self, monkeypatch):
        svc = LlmService(api_key="dummy")

        async def _fake_create(**kwargs):
            raise APIError("upstream broken", request=None, body=None)  # type: ignore[arg-type]

        monkeypatch.setattr(svc.client.chat.completions, "create", _fake_create)
        with pytest.raises(LlmError, match="stream failed"):
            async for _ in svc.generate_stream("SYS", "USR"):
                pass


class TestLlmServiceClient:
    async def test_missing_api_key_raises_on_client_access(self):
        svc = LlmService(api_key="")
        with pytest.raises(LlmError, match="DEEPSEEK_API_KEY"):
            _ = svc.client

    def test_model_id_returns_same_model_for_both_tiers(self):
        svc = LlmService(api_key="dummy")
        assert svc.model_id("flash") == "deepseek-chat"
        assert svc.model_id("pro") == "deepseek-chat"

    def test_back_compat_flash_pro_kwargs_accepted(self):
        # Existing callers/tests still pass these — must not raise TypeError.
        svc = LlmService(
            api_key="dummy", flash_model="gemini-2.0-flash", pro_model="gemini-2.0-pro"
        )
        assert svc._chat_model == "deepseek-chat"
