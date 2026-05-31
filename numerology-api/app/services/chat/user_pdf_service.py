"""End-to-end PDF ingest: hash → match-or-parse → chunk → embed → persist.

Idempotent on (user_id, pdf_hash) — re-uploading the same PDF returns the
existing UserPdfIndex row without re-parsing or re-embedding.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat.user_pdf_chunk import UserPdfChunk
from app.db.models.chat.user_pdf_index import UserPdfIndex, _default_expires_at
from app.db.models.user_report import UserReport
from app.services.chat.chunker import Chunker
from app.services.chat.embedding_service import EmbeddingService
from app.services.chat.pdf_match_service import PdfMatchService, sha256_hex
from app.services.chat.pdf_parser_service import (
    PdfParseError,
    PdfParserService,
)

logger = logging.getLogger(__name__)


@dataclass
class PdfIngestResult:
    pdf_index: UserPdfIndex
    chunks_created: int
    matched: bool
    matched_report_id: Optional[int]
    reused_existing: bool  # True when a prior upload of the same hash was found


class UserPdfService:
    """Orchestrates hybrid match-or-parse PDF ingestion for the chatbot."""

    def __init__(
        self,
        session: AsyncSession,
        embedding_service: EmbeddingService,
        parser: Optional[PdfParserService] = None,
        chunker: Optional[Chunker] = None,
    ) -> None:
        self.session = session
        self.embeddings = embedding_service
        self.parser = parser or PdfParserService()
        self.chunker = chunker or Chunker()
        self.matcher = PdfMatchService(session)

    # -- Public API -------------------------------------------------------

    async def ingest(
        self,
        user_id: int,
        pdf_bytes: bytes,
        filename: Optional[str] = None,
    ) -> PdfIngestResult:
        if not pdf_bytes:
            raise PdfParseError("empty file")

        pdf_hash = sha256_hex(pdf_bytes)

        existing = await self._find_existing_index(user_id, pdf_hash)
        if existing is not None:
            # Slide TTL so actively-used PDFs don't get reaped at the 30d mark.
            existing.expires_at = _default_expires_at()
            await self.session.flush()
            return PdfIngestResult(
                pdf_index=existing,
                chunks_created=0,
                matched=existing.matched_report_id is not None,
                matched_report_id=existing.matched_report_id,
                reused_existing=True,
            )

        matched_report = await self.matcher.find_match(pdf_hash, user_id)

        # Source the text: either from the matched report's stored PDF file,
        # or parse the uploaded bytes directly.
        if matched_report and matched_report.pdf_path and os.path.exists(matched_report.pdf_path):
            with open(matched_report.pdf_path, "rb") as f:
                pages = self.parser.extract_pages(f.read())
        else:
            pages = self.parser.extract_pages(pdf_bytes)

        pdf_index = UserPdfIndex(
            user_id=user_id,
            pdf_hash=pdf_hash,
            matched_report_id=matched_report.id if matched_report else None,
            filename=filename,
            page_count=len(pages),
        )
        self.session.add(pdf_index)
        try:
            await self.session.flush()  # need pdf_index.id for FK
        except IntegrityError:
            # Concurrent ingest of the same hash by the same user. The UNIQUE
            # constraint did its job — re-query the now-existing row and bump
            # its TTL just like the existing-path above.
            await self.session.rollback()
            winner = await self._find_existing_index(user_id, pdf_hash)
            if winner is None:
                raise  # shouldn't happen — surface the original error
            winner.expires_at = _default_expires_at()
            await self.session.flush()
            return PdfIngestResult(
                pdf_index=winner,
                chunks_created=0,
                matched=winner.matched_report_id is not None,
                matched_report_id=winner.matched_report_id,
                reused_existing=True,
            )

        chunks_made = await self._embed_and_persist_pages(pdf_index.id, pages)
        await self.session.flush()

        return PdfIngestResult(
            pdf_index=pdf_index,
            chunks_created=chunks_made,
            matched=matched_report is not None,
            matched_report_id=matched_report.id if matched_report else None,
            reused_existing=False,
        )

    # -- Internals --------------------------------------------------------

    async def _find_existing_index(
        self, user_id: int, pdf_hash: str
    ) -> Optional[UserPdfIndex]:
        stmt = select(UserPdfIndex).where(
            UserPdfIndex.user_id == user_id,
            UserPdfIndex.pdf_hash == pdf_hash,
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def _embed_and_persist_pages(
        self, pdf_index_id: int, pages: list
    ) -> int:
        # Chunk page-by-page so we preserve the page_number for citations.
        chunk_records: list[tuple[int, int, str, int]] = []  # (page_num, chunk_idx, content, tokens)
        global_index = 0
        for page in pages:
            for c in self.chunker.chunk(page.text):
                chunk_records.append((page.page_number, global_index, c.content, c.token_count))
                global_index += 1
        if not chunk_records:
            return 0

        texts = [r[2] for r in chunk_records]
        vectors = await self.embeddings.embed_batch(texts)
        if len(vectors) != len(chunk_records):
            raise RuntimeError(
                f"embedding count mismatch: {len(vectors)} vs {len(chunk_records)}"
            )

        rows = [
            UserPdfChunk(
                pdf_index_id=pdf_index_id,
                chunk_index=chunk_idx,
                content=content,
                embedding=vec,
                token_count=tokens,
                page_number=page_num,
            )
            for (page_num, chunk_idx, content, tokens), vec in zip(chunk_records, vectors)
        ]
        self.session.add_all(rows)
        return len(rows)
