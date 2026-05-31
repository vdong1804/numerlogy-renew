# ruff: noqa: UP045
"""Gemini chat client — non-streaming generate() + async streaming generate_stream().

Uses google-genai (Vertex-AI-style) with asyncio.to_thread for the sync SDK.
Streaming bridges the sync iterator to an async one via asyncio.Queue so the
FastAPI event loop is never blocked.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Literal, Optional

from google import genai
from google.genai import types as genai_types

from app.config import settings

logger = logging.getLogger(__name__)


class LlmError(RuntimeError):
    """Raised when generation fails (timeout, API error, etc)."""


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
    """Thin async wrapper around google-genai for chat generation."""

    def __init__(
        self,
        api_key: str | None = None,
        flash_model: str | None = None,
        pro_model: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self._api_key = api_key or settings.gemini_api_key
        self._flash_model = flash_model or settings.gemini_flash_model
        self._pro_model = pro_model or settings.gemini_pro_model
        self._timeout = timeout or settings.llm_timeout_seconds
        self._client: genai.Client | None = None

    # -- Client lifecycle -------------------------------------------------

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            if not self._api_key:
                raise LlmError("GEMINI_API_KEY is not configured")
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def model_id(self, tier: Literal["flash", "pro"]) -> str:
        return self._pro_model if tier == "pro" else self._flash_model

    # -- Public API -------------------------------------------------------

    async def generate_stream(
        self,
        system: str,
        user_content: str,
        tier: Literal["flash", "pro"] = "flash",
        result: StreamResult | None = None,
        cached_content: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Yield text chunks from a streaming Gemini call.

        Bridges the sync google-genai iterator to an async one via an
        asyncio.Queue.  A background thread runs the SDK iterator and puts
        each text chunk onto the queue; the async consumer awaits each item.

        Token counts and model name are written into `result` (if provided)
        after the stream completes — read them only after the iterator is
        exhausted.

        Raises LlmError if the first token does not arrive within self._timeout
        seconds or if the API raises.

        NOTE (H2 — accepted limitation): the producer thread cannot be
        force-killed on client disconnect.  google-genai's sync iterator has no
        reliable .close() hook, so cancelling the consumer (asyncio.CancelledError
        from FastAPI on client abort) only stops this side; the producer thread
        drains the full LLM response naturally.  The HttpOptions(timeout=...) set
        in _producer() bounds the worst-case thread lifetime to self._timeout seconds.
        """
        model = self.model_id(tier)
        if result is not None:
            result.model_used = model

        # Sentinel object that signals the producer thread is done.
        _DONE = object()
        queue: asyncio.Queue[object] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def _producer() -> None:
            """Run in a worker thread; put text chunks or exception onto queue."""
            try:
                http_opts = genai_types.HttpOptions(timeout=self._timeout * 1000)
                cfg_kwargs: dict = {
                    "system_instruction": system,
                    "http_options": http_opts,
                }
                if cached_content is not None:
                    cfg_kwargs["cached_content"] = cached_content
                stream = self.client.models.generate_content_stream(
                    model=model,
                    contents=user_content,
                    config=genai_types.GenerateContentConfig(**cfg_kwargs),
                )
                for chunk in stream:
                    text = getattr(chunk, "text", None) or ""
                    if text:
                        loop.call_soon_threadsafe(queue.put_nowait, text)
                    # Last chunk carries usage_metadata — capture it.
                    usage = getattr(chunk, "usage_metadata", None)
                    if usage and result is not None:
                        result.input_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
                        result.output_tokens = int(getattr(usage, "candidates_token_count", 0) or 0)
            except Exception as exc:  # noqa: BLE001  # thread context — no CancelledError here
                loop.call_soon_threadsafe(queue.put_nowait, exc)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, _DONE)

        thread = threading.Thread(target=_producer, daemon=True)
        thread.start()

        try:
            # First-token timeout guards against hung API connections.
            first = True
            while True:
                timeout = self._timeout if first else None
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=timeout)
                except asyncio.CancelledError:
                    # Consumer cancelled (client disconnect) — re-raise so
                    # FastAPI handles cleanup; producer drains naturally (see docstring).
                    raise
                except TimeoutError as exc:
                    raise LlmError(
                        f"LLM stream timed out waiting for first token after {self._timeout}s"
                    ) from exc
                first = False

                if item is _DONE:
                    break
                if isinstance(item, BaseException):
                    raise LlmError(f"LLM stream failed: {item}") from item
                yield str(item)  # type: ignore[arg-type]
        finally:
            thread.join(timeout=1)

    async def generate(
        self,
        system: str,
        user_content: str,
        tier: Literal["flash", "pro"] = "flash",
        cached_content: Optional[str] = None,
    ) -> LlmResponse:
        model = self.model_id(tier)
        try:
            return await asyncio.wait_for(
                self._call(model, system, user_content, cached_content=cached_content),
                timeout=self._timeout,
            )
        except TimeoutError as exc:
            raise LlmError(f"LLM timed out after {self._timeout}s") from exc

    # -- Internals --------------------------------------------------------

    async def _call(
        self,
        model: str,
        system: str,
        user_content: str,
        cached_content: Optional[str] = None,
    ) -> LlmResponse:
        # Bound the SYNC google-genai HTTP call too. asyncio.wait_for cancels
        # the awaiting coroutine but does NOT stop the underlying thread/socket;
        # http_options.timeout is what actually frees the socket on the server side.
        http_opts = genai_types.HttpOptions(timeout=self._timeout * 1000)  # ms

        def _sync() -> LlmResponse:
            cfg_kwargs: dict = {
                "system_instruction": system,
                "http_options": http_opts,
            }
            if cached_content is not None:
                cfg_kwargs["cached_content"] = cached_content
            resp = self.client.models.generate_content(
                model=model,
                contents=user_content,
                config=genai_types.GenerateContentConfig(**cfg_kwargs),
            )
            text = (resp.text or "").strip()
            if not text:
                # Safety-blocked or empty response → don't persist a blank bubble.
                raise LlmError("LLM returned empty response (likely safety filter)")
            usage = getattr(resp, "usage_metadata", None)
            in_tok = int(getattr(usage, "prompt_token_count", 0) or 0)
            out_tok = int(getattr(usage, "candidates_token_count", 0) or 0)
            return LlmResponse(
                text=text,
                model_used=model,
                input_tokens=in_tok,
                output_tokens=out_tok,
            )

        try:
            return await asyncio.to_thread(_sync)
        except LlmError:
            raise
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise LlmError(f"LLM call failed: {exc}") from exc
