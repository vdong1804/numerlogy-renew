# ruff: noqa: UP045
"""DeepSeek chat client — non-streaming generate() + async streaming generate_stream().

Uses the OpenAI-compatible SDK pointed at https://api.deepseek.com. The SDK is
async-native (AsyncOpenAI), so streaming runs directly on the event loop with
no thread bridge. Token usage on streams requires
`stream_options={"include_usage": True}` — the final chunk then carries
`usage.prompt_tokens` / `usage.completion_tokens`.

Single-model strategy: `deepseek-chat` serves both the existing `flash` and
`pro` tiers. The `tier` parameter is preserved for caller API stability but
maps to the same model id.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Literal

from openai import APIConnectionError, APIError, APITimeoutError, AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class LlmError(RuntimeError):
    """Raised when generation fails (timeout, API error, empty response, etc)."""


@dataclass
class LlmResponse:
    text: str
    model_used: str
    input_tokens: int
    output_tokens: int


@dataclass
class StreamResult:
    """Sidecar populated after generate_stream() iterator is exhausted.

    The caller awaits the full iterator, then reads token counts from here.
    Usage::

        result = StreamResult()
        async for tok in llm.generate_stream(sys, usr, result=result):
            ...
        print(result.input_tokens, result.output_tokens)
    """

    input_tokens: int = field(default=0)
    output_tokens: int = field(default=0)
    model_used: str = field(default="")


class LlmService:
    """Thin async wrapper around the OpenAI-compatible DeepSeek API."""

    def __init__(
        self,
        api_key: str | None = None,
        # flash_model / pro_model accepted for back-compat (tests still pass them);
        # both tiers map to settings.deepseek_chat_model under the single-model strategy.
        flash_model: str | None = None,  # noqa: ARG002
        pro_model: str | None = None,  # noqa: ARG002
        timeout: int | None = None,
        chat_model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self._api_key = api_key or settings.deepseek_api_key
        self._chat_model = chat_model or settings.deepseek_chat_model
        self._base_url = base_url or settings.deepseek_base_url
        self._timeout = timeout or settings.llm_timeout_seconds
        self._client: AsyncOpenAI | None = None

    # -- Client lifecycle -------------------------------------------------

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            if not self._api_key:
                raise LlmError("DEEPSEEK_API_KEY is not configured")
            self._client = AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)
        return self._client

    def model_id(self, tier: Literal["flash", "pro"]) -> str:  # noqa: ARG002
        """Return the chat model id. `tier` is accepted for caller API stability
        but both tiers resolve to the same DeepSeek model under the single-model strategy."""
        return self._chat_model

    # -- Public API -------------------------------------------------------

    async def generate_stream(
        self,
        system: str,
        user_content: str,
        tier: Literal["flash", "pro"] = "flash",  # noqa: ARG002
        result: StreamResult | None = None,
    ) -> AsyncIterator[str]:
        """Yield text chunks from a streaming DeepSeek call.

        Populates `result` (if provided) with token counts and model id once
        the final chunk arrives. Raises LlmError on API failure or timeout.
        On client disconnect (asyncio.CancelledError) propagates the
        cancellation — the underlying httpx stream is closed by the SDK.
        """
        model = self._chat_model
        if result is not None:
            result.model_used = model

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ]

        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore[arg-type]
                stream=True,
                stream_options={"include_usage": True},
                timeout=self._timeout,
            )
            async for chunk in stream:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    text = getattr(delta, "content", None) or ""
                    if text:
                        yield text
                # `usage` only appears on the final chunk when include_usage=True
                usage = getattr(chunk, "usage", None)
                if usage and result is not None:
                    result.input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
                    result.output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        except APITimeoutError as exc:
            raise LlmError(f"LLM stream timed out after {self._timeout}s") from exc
        except (APIError, APIConnectionError) as exc:
            raise LlmError(f"LLM stream failed: {exc}") from exc
        except asyncio.CancelledError:
            raise

    async def generate(
        self,
        system: str,
        user_content: str,
        tier: Literal["flash", "pro"] = "flash",  # noqa: ARG002
    ) -> LlmResponse:
        model = self._chat_model
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ]
        try:
            resp = await self.client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore[arg-type]
                stream=False,
                timeout=self._timeout,
            )
        except APITimeoutError as exc:
            raise LlmError(f"LLM timed out after {self._timeout}s") from exc
        except (APIError, APIConnectionError) as exc:
            raise LlmError(f"LLM call failed: {exc}") from exc
        except asyncio.CancelledError:
            raise

        text = (resp.choices[0].message.content or "").strip() if resp.choices else ""
        if not text:
            # Safety-blocked or empty response → don't persist a blank bubble.
            raise LlmError("LLM returned empty response (likely safety filter)")
        usage = resp.usage
        in_tok = int(getattr(usage, "prompt_tokens", 0) or 0) if usage else 0
        out_tok = int(getattr(usage, "completion_tokens", 0) or 0) if usage else 0
        return LlmResponse(
            text=text,
            model_used=model,
            input_tokens=in_tok,
            output_tokens=out_tok,
        )
