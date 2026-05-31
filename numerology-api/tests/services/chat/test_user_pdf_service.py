"""Integration tests for UserPdfService — sqlite + mocked parser/embeddings."""

import pytest
from sqlalchemy import select

from app.db.models.chat.user_pdf_chunk import UserPdfChunk
from app.db.models.chat.user_pdf_index import UserPdfIndex
from app.db.models.user_report import UserReport
from app.services.chat.chunker import Chunker
from app.services.chat.embedding_service import EmbeddingService
from app.services.chat.pdf_match_service import sha256_hex
from app.services.chat.pdf_parser_service import PageText
from app.services.chat.user_pdf_service import UserPdfService


class _FakeParser:
    def __init__(self, pages: list[PageText]) -> None:
        self._pages = pages

    def extract_pages(self, pdf_bytes: bytes) -> list[PageText]:  # noqa: ARG002
        return list(self._pages)


class _FakeEmbeddings(EmbeddingService):
    """Returns deterministic 768-dim zero vectors."""

    def __init__(self) -> None:
        self._api_key = "fake"
        self._model = "fake"
        self._batch_size = 100
        self._max_retries = 1
        self._client = None
        self.batch_calls: list[int] = []

    async def embed_batch(self, texts):
        self.batch_calls.append(len(texts))
        return [[0.0] * 768 for _ in texts]


def _pages(content: str = "paragraph one " * 30, n: int = 2) -> list[PageText]:
    return [PageText(page_number=i + 1, text=content) for i in range(n)]


def _make_svc(db, parser=None, embeddings=None) -> UserPdfService:
    return UserPdfService(
        db,
        embedding_service=embeddings or _FakeEmbeddings(),
        parser=parser or _FakeParser(_pages()),
        chunker=Chunker(max_tokens=80, overlap_tokens=0),
    )


@pytest.mark.asyncio
async def test_ingest_creates_index_and_chunks(db_session, user):
    svc = _make_svc(db_session)
    result = await svc.ingest(user.id, b"%PDF-1.4 fake bytes", filename="report.pdf")
    await db_session.commit()

    assert result.reused_existing is False
    assert result.chunks_created >= 1
    assert result.pdf_index.user_id == user.id
    assert result.pdf_index.filename == "report.pdf"
    assert result.pdf_index.page_count == 2

    chunks = (await db_session.execute(
        select(UserPdfChunk).where(UserPdfChunk.pdf_index_id == result.pdf_index.id)
    )).scalars().all()
    assert len(chunks) == result.chunks_created
    assert all(c.page_number in (1, 2) for c in chunks)


@pytest.mark.asyncio
async def test_ingest_same_hash_reuses_existing(db_session, user):
    embeddings = _FakeEmbeddings()
    svc = _make_svc(db_session, embeddings=embeddings)
    pdf_bytes = b"%PDF-1.4 same content"

    first = await svc.ingest(user.id, pdf_bytes)
    await db_session.commit()
    second = await svc.ingest(user.id, pdf_bytes)
    await db_session.commit()

    assert second.reused_existing is True
    assert second.pdf_index.id == first.pdf_index.id
    assert second.chunks_created == 0
    # Embedding API was called only on the first ingest
    assert len(embeddings.batch_calls) == 1


@pytest.mark.asyncio
async def test_ingest_matches_existing_user_report(db_session, user):
    pdf_bytes = b"%PDF-1.4 matched report"
    pdf_hash = sha256_hex(pdf_bytes)
    # Pre-create a UserReport with this hash
    db_session.add(UserReport(
        user_id=user.id,
        product_id=1,
        pdf_path="/tmp/does-not-exist.pdf",
        file_hash=pdf_hash,
        input_payload={},
    ))
    await db_session.flush()

    svc = _make_svc(db_session)
    result = await svc.ingest(user.id, pdf_bytes)
    await db_session.commit()

    assert result.matched is True
    assert result.matched_report_id is not None
    assert result.pdf_index.matched_report_id == result.matched_report_id


@pytest.mark.asyncio
async def test_ingest_slides_ttl_on_reupload(db_session, user):
    from datetime import datetime, timedelta, timezone

    svc = _make_svc(db_session)
    pdf_bytes = b"%PDF-1.4 slide ttl test"

    first = await svc.ingest(user.id, pdf_bytes)
    await db_session.commit()
    # Backdate the row to simulate a near-expiry entry
    first.pdf_index.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    await db_session.commit()

    second = await svc.ingest(user.id, pdf_bytes)
    await db_session.commit()
    assert second.reused_existing is True
    # TTL should have been bumped to ~30 days out
    assert second.pdf_index.expires_at > datetime.now(timezone.utc) + timedelta(days=29)


@pytest.mark.asyncio
async def test_ingest_empty_bytes_raises(db_session, user):
    from app.services.chat.pdf_parser_service import PdfParseError

    svc = _make_svc(db_session)
    with pytest.raises(PdfParseError):
        await svc.ingest(user.id, b"")


@pytest.mark.asyncio
async def test_ingest_isolation_two_users_same_bytes(db_session, user, superuser):
    pdf_bytes = b"%PDF-1.4 same bytes both users"
    svc = _make_svc(db_session)
    r1 = await svc.ingest(user.id, pdf_bytes)
    r2 = await svc.ingest(superuser.id, pdf_bytes)
    await db_session.commit()

    # Each user gets their own UserPdfIndex row even though hashes match
    assert r1.pdf_index.id != r2.pdf_index.id
    assert r1.pdf_index.user_id == user.id
    assert r2.pdf_index.user_id == superuser.id

    rows = (await db_session.execute(select(UserPdfIndex))).scalars().all()
    assert len(rows) == 2
