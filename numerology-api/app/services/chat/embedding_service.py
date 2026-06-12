"""Gemini text-embedding-004 wrapper with batching + exponential-backoff retry.

The Gemini API accepts a list of strings per call; we cap each request at
`embedding_batch_size` to stay under the per-request size limit and keep
retries cheap. Retries are exponential (1s, 2s, 4s) and only fire on
transient failures (network / 5xx) — auth / 4xx propagate immediately.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import tiktoken
from google import genai
from google.genai import types as genai_types

from app.config import settings
from app.services.genai_client import build_genai_client, is_genai_configured

logger = logging.getLogger(__name__)

# HTTP status codes that indicate transient failures worth retrying.
_RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})

# Last-resort substring match for SDK errors that don't expose a code attribute.
# Word-bounded to avoid matching "500-character" or "internal validation".
_RETRYABLE_TOKENS = (
    "deadline exceeded",
    "deadline_exceeded",
    "service unavailable",
    "service_unavailable",
    "resource exhausted",
    "resource_exhausted",
    "internal server error",
    "rate limit",
    "rate_limit",
)


class EmbeddingError(RuntimeError):
    """Raised when the embedding API fails after all retries."""


class EmbeddingService:
    """Thin async wrapper around the Gemini embedding endpoint."""

    def __init__(
        self,
        model: Optional[str] = None,
        batch_size: Optional[int] = None,
        max_retries: int = 3,
        max_request_tokens: Optional[int] = None,
    ) -> None:
        self._model = model or settings.embedding_model
        self._batch_size = batch_size or settings.embedding_batch_size
        self._max_request_tokens = (
            max_request_tokens or settings.embedding_max_request_tokens
        )
        self._max_retries = max_retries
        # Same tokenizer the Chunker uses — only for request-budget packing.
        self._enc = tiktoken.get_encoding("cl100k_base")
        # Defer client creation; tests inject a mock client via `_client`
        self._client: Optional[genai.Client] = None

    # -- Client lifecycle -------------------------------------------------

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            if not is_genai_configured():
                raise EmbeddingError(
                    "no genai auth: set google_application_credentials "
                    "(Vertex AI service account)"
                )
            self._client = build_genai_client()
        return self._client

    # -- Public API -------------------------------------------------------

    async def embed_one(self, text: str) -> list[float]:
        vectors = await self.embed_batch([text])
        return vectors[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed N texts; splits into request-sized windows transparently.

        Windows are bounded by BOTH a max count (``batch_size``) and a max
        total token count (``max_request_tokens``). The token bound is the one
        that matters for Vertex text-embedding-004: it rejects any request
        whose summed input tokens exceed 20000, regardless of text count.
        """
        if not texts:
            return []
        out: list[list[float]] = []
        window: list[str] = []
        window_tokens = 0
        for text in texts:
            tok = len(self._enc.encode(text))
            # Flush the current window before it would breach either cap.
            if window and (
                len(window) >= self._batch_size
                or window_tokens + tok > self._max_request_tokens
            ):
                out.extend(await self._embed_with_retry(window))
                window, window_tokens = [], 0
            window.append(text)
            window_tokens += tok
        if window:
            out.extend(await self._embed_with_retry(window))
        return out

    # -- Internals --------------------------------------------------------

    async def _embed_with_retry(self, texts: list[str]) -> list[list[float]]:
        last_exc: Optional[Exception] = None
        for attempt in range(self._max_retries):
            try:
                return await self._call_api(texts)
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if not self._is_retryable(exc) or attempt == self._max_retries - 1:
                    break
                delay = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(
                    "embed retry %d/%d after error: %s (sleep %ss)",
                    attempt + 1, self._max_retries, exc, delay,
                )
                await asyncio.sleep(delay)
        raise EmbeddingError(f"embedding failed after {self._max_retries} attempts: {last_exc}")

    async def _call_api(self, texts: list[str]) -> list[list[float]]:
        # google-genai client is sync; offload to thread to keep async semantics
        def _sync_call() -> list[list[float]]:
            resp = self.client.models.embed_content(
                model=self._model,
                contents=texts,
                config=genai_types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
            )
            return [list(e.values) for e in resp.embeddings]

        return await asyncio.to_thread(_sync_call)

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        """Prefer typed status codes; fall back to bounded substring tokens."""
        # google-genai surfaces APIError with .code attribute (HTTP status)
        code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        if isinstance(code, int) and code in _RETRYABLE_STATUS_CODES:
            return True
        msg = str(exc).lower()
        return any(tok in msg for tok in _RETRYABLE_TOKENS)
