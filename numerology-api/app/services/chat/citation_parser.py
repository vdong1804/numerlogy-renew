"""Parse [N] markers from the LLM answer and map back to retrieved chunks.

Frontend keeps the [N] markers in the rendered text and overlays citation
tooltips. Only indices that actually appear in the answer become citations
in the response payload — keeps the citation list tight.
"""

from __future__ import annotations

import re

from app.schemas.chat.message import Citation
from app.schemas.chat.retrieval import RetrievedChunk

_CITE_RE = re.compile(r"\[(\d+)\]")


def extract_used_indices(text: str) -> list[int]:
    """Return unique [N] indices in order of first appearance."""
    seen: set[int] = set()
    out: list[int] = []
    for m in _CITE_RE.finditer(text or ""):
        idx = int(m.group(1))
        if idx not in seen:
            seen.add(idx)
            out.append(idx)
    return out


def build_citations(text: str, chunks: list[RetrievedChunk]) -> list[Citation]:
    """Map the [N] markers found in `text` to entries in `chunks` (1-indexed).

    Out-of-range indices (e.g. the model hallucinated [9] when only 3 chunks
    were provided) are silently dropped.
    """
    citations: list[Citation] = []
    for idx in extract_used_indices(text):
        if 1 <= idx <= len(chunks):
            c = chunks[idx - 1]
            citations.append(
                Citation(
                    index=idx,
                    chunk_id=c.chunk_id,
                    document_id=c.document_id,
                    source_type=c.source_type,
                    source_ref=c.source_ref,
                    title=c.title,
                    score=c.score,
                )
            )
    return citations
