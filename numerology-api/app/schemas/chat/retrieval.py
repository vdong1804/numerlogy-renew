"""Retrieval DTO — one KB chunk returned by RetrievalService.

Pure dataclass-like Pydantic model so it can carry both the row data and the
computed similarity score for downstream prompt + citation use.
"""

from typing import Optional

from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    chunk_id: int
    document_id: int
    source_type: str
    source_ref: str
    title: Optional[str]
    content: str
    score: float  # 1 - cosine_distance, range [0, 1]
