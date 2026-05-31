# ruff: noqa: UP045, UP017
"""KB ingestion: chunk text → embed → upsert KbDocument + KbChunks atomically.

`upsert_document` is the single entry point: pass (source_type, source_ref,
title, content, metadata) and the service handles new vs. update by replacing
all existing chunks for the document in one transaction.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat.kb_chunk import KbChunk
from app.db.models.chat.kb_document import KbDocument
from app.services.chat.chunker import Chunker
from app.services.chat.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class KbIngestionService:
    """Idempotent ingestion: upsert by (source_type, source_ref)."""

    def __init__(
        self,
        session: AsyncSession,
        embedding_service: EmbeddingService,
        chunker: Optional[Chunker] = None,
    ) -> None:
        self.session = session
        self.embeddings = embedding_service
        self.chunker = chunker or Chunker()

    # -- Public API -------------------------------------------------------

    async def upsert_document(
        self,
        source_type: str,
        source_ref: str,
        title: Optional[str],
        content: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> KbDocument:
        doc = await self._get_or_create_document(source_type, source_ref, title, metadata)
        await self._replace_chunks(doc, content)
        return doc

    async def reindex_document(self, document_id: int, content: str) -> None:
        doc = await self.session.get(KbDocument, document_id)
        if not doc:
            raise ValueError(f"KbDocument {document_id} not found")
        await self._replace_chunks(doc, content)

    async def delete_document(self, source_type: str, source_ref: str) -> bool:
        doc = await self._find_document(source_type, source_ref)
        if not doc:
            return False
        # FK ON DELETE CASCADE removes chunks
        await self.session.delete(doc)
        await self.session.flush()
        return True

    # -- Internals --------------------------------------------------------

    async def _find_document(
        self, source_type: str, source_ref: str
    ) -> Optional[KbDocument]:
        stmt = select(KbDocument).where(
            KbDocument.source_type == source_type,
            KbDocument.source_ref == source_ref,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def _get_or_create_document(
        self,
        source_type: str,
        source_ref: str,
        title: Optional[str],
        metadata: Optional[dict[str, Any]],
    ) -> KbDocument:
        doc = await self._find_document(source_type, source_ref)
        if doc is None:
            doc = KbDocument(
                source_type=source_type,
                source_ref=source_ref,
                title=title,
                doc_metadata=metadata or {},
            )
            self.session.add(doc)
            await self.session.flush()
            return doc
        # update mutable fields if changed
        if title is not None and doc.title != title:
            doc.title = title
        if metadata is not None:
            doc.doc_metadata = metadata
        await self.session.flush()
        return doc

    @staticmethod
    def _hash_chunks(chunks) -> str:
        """SHA-256 of sorted chunk contents — used for no-op detection."""
        joined = "\n---\n".join(c.content for c in sorted(chunks, key=lambda c: c.index))
        return hashlib.sha256(joined.encode()).hexdigest()

    async def _replace_chunks(self, doc: KbDocument, content: str) -> None:
        """Delete existing chunks then insert freshly-embedded chunks.

        Short-circuits when the new content hash matches the stored chunks hash
        to prevent spurious prompt-cache invalidation on unchanged content.
        """
        chunks = self.chunker.chunk(content)
        if not chunks:
            logger.warning("kb ingestion: empty content for doc id=%s", doc.id)
            await self.session.execute(delete(KbChunk).where(KbChunk.document_id == doc.id))
            await self.session.flush()
            return

        # Check if content is unchanged to avoid unnecessary delete+reinsert
        # which would trigger prompt-cache invalidation (C1 fix).
        new_hash = self._hash_chunks(chunks)
        existing_result = await self.session.execute(
            select(KbChunk)
            .where(KbChunk.document_id == doc.id)
            .order_by(KbChunk.chunk_index)
        )
        existing_chunks = existing_result.scalars().all()
        if existing_chunks:
            old_hash = hashlib.sha256(
                "\n---\n".join(c.content for c in existing_chunks).encode()
            ).hexdigest()
            if old_hash == new_hash:
                logger.debug(
                    "kb ingestion: content unchanged for doc id=%s; skipping replace", doc.id
                )
                return

        texts = [c.content for c in chunks]
        vectors = await self.embeddings.embed_batch(texts)
        if len(vectors) != len(chunks):
            raise RuntimeError(
                f"embedding count mismatch: got {len(vectors)} vectors for {len(chunks)} chunks"
            )

        await self.session.execute(delete(KbChunk).where(KbChunk.document_id == doc.id))
        rows = [
            KbChunk(
                document_id=doc.id,
                chunk_index=c.index,
                content=c.content,
                embedding=vec,
                token_count=c.token_count,
            )
            for c, vec in zip(chunks, vectors)
        ]
        self.session.add_all(rows)
        await self.session.flush()
