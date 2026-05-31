"""Integration tests for KbIngestionService against in-memory SQLite.

EmbeddingService is mocked — we don't hit Gemini. Vector(768) is stored as a
string by pgvector's bind processor on non-pg dialects, which SQLite tolerates.
"""

from typing import Optional

import pytest
from sqlalchemy import select

from app.db.models.chat.kb_chunk import KbChunk
from app.db.models.chat.kb_document import KbDocument
from app.services.chat.chunker import Chunker
from app.services.chat.embedding_service import EmbeddingService
from app.services.chat.kb_ingestion_service import KbIngestionService


class _FakeEmbeddings(EmbeddingService):
    """Returns deterministic vectors without calling Gemini."""

    def __init__(self) -> None:
        # Bypass parent __init__ to avoid API-key validation
        self._api_key = "fake"
        self._model = "fake"
        self._batch_size = 100
        self._max_retries = 1
        self._client = None
        self.calls: list[list[str]] = []

    async def embed_batch(self, texts):
        self.calls.append(list(texts))
        # 768-dim zero vector so the column type is happy
        return [[0.0] * 768 for _ in texts]


def _content(n_paras: int) -> str:
    return "\n\n".join(f"Paragraph {i} " + "word " * 60 for i in range(n_paras))


@pytest.fixture
def fake_embeddings() -> _FakeEmbeddings:
    return _FakeEmbeddings()


@pytest.fixture
def svc(db_session, fake_embeddings) -> KbIngestionService:
    return KbIngestionService(
        session=db_session,
        embedding_service=fake_embeddings,
        chunker=Chunker(max_tokens=80, overlap_tokens=10),
    )


@pytest.mark.asyncio
async def test_upsert_creates_document_and_chunks(svc, db_session):
    doc = await svc.upsert_document(
        source_type="numerology:mission_number",
        source_ref="MN_1",
        title="Mission 1",
        content=_content(3),
    )
    await db_session.commit()

    assert doc.id is not None
    chunks = (await db_session.execute(
        select(KbChunk).where(KbChunk.document_id == doc.id)
    )).scalars().all()
    assert len(chunks) >= 1
    assert all(c.token_count > 0 for c in chunks)
    assert [c.chunk_index for c in chunks] == sorted(c.chunk_index for c in chunks)


@pytest.mark.asyncio
async def test_re_upsert_replaces_old_chunks(svc, db_session, fake_embeddings):
    await svc.upsert_document("numerology:x", "X1", "T", _content(4))
    await db_session.commit()
    first_count = (await db_session.execute(
        select(KbChunk)
    )).scalars().all()
    assert len(first_count) >= 1

    # Second upsert with shorter content → fewer chunks expected
    await svc.upsert_document("numerology:x", "X1", "T", "short paragraph only")
    await db_session.commit()
    docs = (await db_session.execute(
        select(KbDocument).where(KbDocument.source_ref == "X1")
    )).scalars().all()
    assert len(docs) == 1  # still one doc (idempotent on natural key)

    chunks = (await db_session.execute(
        select(KbChunk).where(KbChunk.document_id == docs[0].id)
    )).scalars().all()
    assert len(chunks) == 1  # one short chunk

    # Embedding service called twice (once per upsert)
    assert len(fake_embeddings.calls) == 2


@pytest.mark.asyncio
async def test_delete_document_removes_doc_and_chunks(svc, db_session):
    await svc.upsert_document("numerology:y", "Y1", "T", _content(2))
    await db_session.commit()

    ok = await svc.delete_document("numerology:y", "Y1")
    await db_session.commit()
    assert ok is True

    remaining = (await db_session.execute(
        select(KbDocument).where(KbDocument.source_ref == "Y1")
    )).scalars().all()
    assert remaining == []


@pytest.mark.asyncio
async def test_delete_missing_returns_false(svc):
    assert await svc.delete_document("numerology:z", "nope") is False


@pytest.mark.asyncio
async def test_empty_content_deletes_existing_chunks(svc, db_session):
    await svc.upsert_document("numerology:e", "E1", "T", _content(2))
    await db_session.commit()
    pre = (await db_session.execute(select(KbChunk))).scalars().all()
    assert len(pre) >= 1

    await svc.upsert_document("numerology:e", "E1", "T", "")
    await db_session.commit()
    post = (await db_session.execute(select(KbChunk))).scalars().all()
    assert post == []


@pytest.mark.asyncio
async def test_replace_chunks_no_op_when_content_unchanged(svc, db_session, fake_embeddings):
    """C1 fix: re-upsert with identical content must NOT call embed or delete+reinsert."""
    content = _content(3)
    await svc.upsert_document("numerology:noop", "N1", "T", content)
    await db_session.commit()
    embed_calls_after_first = len(fake_embeddings.calls)

    # Second upsert with same content — should short-circuit before embedding
    await svc.upsert_document("numerology:noop", "N1", "T", content)
    await db_session.commit()

    # No new embedding call should have been made
    assert len(fake_embeddings.calls) == embed_calls_after_first, (
        "embed_batch should not be called when chunk content is unchanged"
    )

    # Chunks remain present and unchanged
    docs = (await db_session.execute(
        select(KbDocument).where(KbDocument.source_ref == "N1")
    )).scalars().all()
    chunks = (await db_session.execute(
        select(KbChunk).where(KbChunk.document_id == docs[0].id)
    )).scalars().all()
    assert len(chunks) >= 1
