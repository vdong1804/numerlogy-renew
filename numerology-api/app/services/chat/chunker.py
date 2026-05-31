"""Token-aware text splitter for KB ingestion.

Strategy:
1. Split source text by paragraph (blank-line separator).
2. Greedily pack paragraphs into a window of `max_tokens`.
3. If a single paragraph exceeds the window, fall back to sentence packing.
4. Adjacent windows share `overlap_tokens` to preserve context across chunks.

tiktoken cl100k_base sizing is ~10% off Gemini's tokenizer but close enough
for chunk-size budgeting (verified in plan risk row).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import tiktoken

from app.config import settings

_PARA_SPLIT = re.compile(r"\n\s*\n")
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


@dataclass
class TextChunk:
    index: int
    content: str
    token_count: int


class Chunker:
    """Pack text into ≤ max_tokens chunks with `overlap_tokens` overlap."""

    def __init__(
        self,
        max_tokens: Optional[int] = None,
        overlap_tokens: Optional[int] = None,
        encoding_name: str = "cl100k_base",
    ) -> None:
        # Use `is None` (not `or`) so callers can pass 0 to disable overlap.
        self.max_tokens = settings.chunk_max_tokens if max_tokens is None else max_tokens
        self.overlap_tokens = (
            settings.chunk_overlap_tokens if overlap_tokens is None else overlap_tokens
        )
        self._enc = tiktoken.get_encoding(encoding_name)

    # -- Public API -------------------------------------------------------

    def count_tokens(self, text: str) -> int:
        return len(self._enc.encode(text))

    def chunk(self, text: str) -> list[TextChunk]:
        text = (text or "").strip()
        if not text:
            return []

        units = self._split_into_units(text)
        windows = self._pack(units)
        windows = self._apply_overlap(windows)
        return [
            TextChunk(index=i, content=w, token_count=self.count_tokens(w))
            for i, w in enumerate(windows)
        ]

    # -- Internals --------------------------------------------------------

    def _split_into_units(self, text: str) -> list[str]:
        """Paragraph first; oversize paragraphs split into sentences."""
        units: list[str] = []
        for para in _PARA_SPLIT.split(text):
            para = para.strip()
            if not para:
                continue
            if self.count_tokens(para) <= self.max_tokens:
                units.append(para)
            else:
                for sent in _SENT_SPLIT.split(para):
                    sent = sent.strip()
                    if sent:
                        units.append(sent)
        return units

    def _pack(self, units: list[str]) -> list[str]:
        windows: list[str] = []
        buf: list[str] = []
        buf_tokens = 0
        for unit in units:
            t = self.count_tokens(unit)
            if buf and buf_tokens + t > self.max_tokens:
                windows.append("\n\n".join(buf))
                buf, buf_tokens = [], 0
            buf.append(unit)
            buf_tokens += t
        if buf:
            windows.append("\n\n".join(buf))
        return windows

    def _apply_overlap(self, windows: list[str]) -> list[str]:
        """Prepend `overlap_tokens` worth of previous chunk's tail to each window."""
        if self.overlap_tokens <= 0 or len(windows) < 2:
            return windows
        out = [windows[0]]
        for i in range(1, len(windows)):
            prev_tail = self._tail_tokens(windows[i - 1], self.overlap_tokens)
            out.append(f"{prev_tail}\n\n{windows[i]}" if prev_tail else windows[i])
        return out

    def _tail_tokens(self, text: str, n: int) -> str:
        ids = self._enc.encode(text)
        if len(ids) <= n:
            return text
        return self._enc.decode(ids[-n:])
