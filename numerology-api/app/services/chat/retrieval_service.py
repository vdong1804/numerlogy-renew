"""KB + user-PDF retrieval — pgvector top-k cosine with hybrid merge.

When `pdf_context_id` is None: KB-only search over `kb_chunks` (Phase 02 behavior).
When provided: query both `kb_chunks` and `user_pdf_chunks` for the same query
embedding, take roughly half top_k from each, and merge by similarity score.

The user-PDF arm is restricted to the given `pdf_context_id` so a user can
never read another user's chunks even if they guess an int — the upload
router validates ownership before calling here.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.schemas.chat.retrieval import RetrievedChunk
from app.services.chat.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class RetrievalService:
    """Top-k semantic search over kb_chunks + (optionally) user_pdf_chunks."""

    def __init__(
        self,
        session: AsyncSession,
        embedding_service: EmbeddingService,
    ) -> None:
        self.session = session
        self.embeddings = embedding_service

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        pdf_context_id: Optional[int] = None,
    ) -> list[RetrievedChunk]:
        if not query.strip():
            return []

        k = top_k if top_k is not None else settings.rag_top_k_free
        thresh = threshold if threshold is not None else settings.rag_sim_threshold

        query_emb = await self.embeddings.embed_one(query)
        if pdf_context_id is None:
            return await self._search_kb(query_emb, k, thresh)
        return await self._search_hybrid(query_emb, k, thresh, pdf_context_id)

    # -- KB-only search ---------------------------------------------------

    async def _search_kb(
        self, query_emb: list[float], top_k: int, threshold: float
    ) -> list[RetrievedChunk]:
        emb_str = self._vector_literal(query_emb)
        sql = text(
            """
            SELECT
                c.id            AS chunk_id,
                c.document_id   AS document_id,
                d.source_type   AS source_type,
                d.source_ref    AS source_ref,
                d.title         AS title,
                c.content       AS content,
                1 - (c.embedding <=> CAST(:emb AS vector)) AS score
            FROM kb_chunks c
            JOIN kb_documents d ON d.id = c.document_id
            ORDER BY c.embedding <=> CAST(:emb AS vector) ASC
            LIMIT :k
            """
        )
        result = await self.session.execute(sql, {"emb": emb_str, "k": top_k})
        return self._rows_to_chunks(result.mappings().all(), threshold)

    # -- Hybrid KB + user-PDF search --------------------------------------

    async def _search_hybrid(
        self,
        query_emb: list[float],
        top_k: int,
        threshold: float,
        pdf_context_id: int,
    ) -> list[RetrievedChunk]:
        # PDF-favored split: when a user attaches a PDF they want answers about
        # THEIR doc, so PDF gets the larger share. top_k=3 → 2 PDF + 1 KB
        # (matches plan §requirements "2 KB + 3 PDF" PDF-heavy ratio scaled to
        # free-tier budget). top_k=1 collapses to PDF-only.
        if top_k <= 1:
            pdf_k, kb_k = top_k, 0
        else:
            pdf_k = (top_k + 1) // 2
            kb_k = top_k - pdf_k  # guaranteed >= 1 when top_k >= 2
        emb_str = self._vector_literal(query_emb)

        kb_rows = []
        if kb_k > 0:
            kb_rows = (await self.session.execute(
                text(
                    """
                    SELECT
                        c.id            AS chunk_id,
                        c.document_id   AS document_id,
                        d.source_type   AS source_type,
                        d.source_ref    AS source_ref,
                        d.title         AS title,
                        c.content       AS content,
                        1 - (c.embedding <=> CAST(:emb AS vector)) AS score
                    FROM kb_chunks c
                    JOIN kb_documents d ON d.id = c.document_id
                    ORDER BY c.embedding <=> CAST(:emb AS vector) ASC
                    LIMIT :k
                    """
                ),
                {"emb": emb_str, "k": kb_k},
            )).mappings().all()

        pdf_rows = (await self.session.execute(
            text(
                """
                SELECT
                    c.id            AS chunk_id,
                    c.pdf_index_id  AS document_id,
                    'user_pdf'      AS source_type,
                    CAST(c.page_number AS TEXT) AS source_ref,
                    i.filename      AS title,
                    c.content       AS content,
                    1 - (c.embedding <=> CAST(:emb AS vector)) AS score
                FROM user_pdf_chunks c
                JOIN user_pdf_index i ON i.id = c.pdf_index_id
                WHERE c.pdf_index_id = :pdf_index_id
                ORDER BY c.embedding <=> CAST(:emb AS vector) ASC
                LIMIT :k
                """
            ),
            {"emb": emb_str, "k": pdf_k, "pdf_index_id": pdf_context_id},
        )).mappings().all()

        merged = self._rows_to_chunks(kb_rows, threshold) + self._rows_to_chunks(
            pdf_rows, threshold
        )
        merged.sort(key=lambda c: c.score, reverse=True)
        return merged[:top_k]

    # -- Helpers ----------------------------------------------------------

    @staticmethod
    def _rows_to_chunks(rows, threshold: float) -> list[RetrievedChunk]:
        return [
            RetrievedChunk(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                source_type=row["source_type"],
                source_ref=row["source_ref"] if row["source_ref"] is not None else "",
                title=row["title"],
                content=row["content"],
                score=float(row["score"]),
            )
            for row in rows
            if float(row["score"]) >= threshold
        ]

    @staticmethod
    def _vector_literal(vec: list[float]) -> str:
        return "[" + ",".join(f"{float(v):.8f}" for v in vec) + "]"
