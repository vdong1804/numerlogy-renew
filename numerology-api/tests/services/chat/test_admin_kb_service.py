"""Unit tests for AdminKbService — file-kind detection + extraction + ingest path."""

from __future__ import annotations

import pytest

from app.services.chat.admin_kb_service import (
    AdminKbService,
    ExtractedEmpty,
    UnsupportedFileType,
    MAX_EXTRACTED_CHARS,
)
from app.services.chat.chunker import Chunker
from app.services.chat.embedding_service import EmbeddingService
from app.services.chat.kb_ingestion_service import KbIngestionService


class _FakeEmbeddings(EmbeddingService):
    def __init__(self) -> None:
        self._model = "fake"
        self._batch_size = 100
        self._max_retries = 1
        self._client = None

    async def embed_batch(self, texts):
        return [[0.0] * 768 for _ in texts]


@pytest.fixture
def svc(db_session) -> AdminKbService:
    kb = KbIngestionService(
        db_session,
        _FakeEmbeddings(),
        Chunker(max_tokens=80, overlap_tokens=10),
    )
    return AdminKbService(db_session, kb)


def test_extract_txt_utf8(svc):
    data = "Hello world\nĐây là tiếng Việt.".encode("utf-8")
    out = svc.extract("notes.txt", data)
    assert out.file_kind == "txt"
    assert "tiếng Việt" in out.text
    assert out.char_count == len(out.text)


def test_extract_txt_strips_bom(svc):
    data = b"\xef\xbb\xbfhello"
    out = svc.extract("notes.txt", data)
    assert out.text == "hello"


def test_extract_md_treated_as_txt(svc):
    data = b"# Heading\n\nbody text"
    out = svc.extract("doc.md", data)
    assert out.file_kind == "txt"
    assert "Heading" in out.text


def test_unsupported_extension(svc):
    with pytest.raises(UnsupportedFileType):
        svc.extract("evil.exe", b"\x00\x00")


def test_empty_file(svc):
    with pytest.raises(ExtractedEmpty):
        svc.extract("notes.txt", b"")


def test_truncates_oversize_text(svc):
    data = ("a" * (MAX_EXTRACTED_CHARS + 5_000)).encode("utf-8")
    out = svc.extract("big.txt", data)
    assert out.char_count == MAX_EXTRACTED_CHARS


@pytest.mark.asyncio
async def test_ingest_upload_creates_admin_doc(svc, db_session):
    body = ("paragraph " * 50).encode("utf-8")
    doc = await svc.ingest_upload(
        filename="welcome.txt",
        file_bytes=body,
        admin_id=42,
        title="Welcome doc",
    )
    assert doc.source_type == "admin_upload"
    assert doc.source_ref == "42-welcome.txt"
    assert doc.title == "Welcome doc"
    assert doc.created_by == 42
    assert doc.doc_metadata["file_kind"] == "txt"
    assert doc.doc_metadata["uploaded_by"] == 42


@pytest.mark.asyncio
async def test_ingest_upload_idempotent_by_filename(svc, db_session):
    body1 = ("first " * 80).encode("utf-8")
    body2 = ("second " * 80).encode("utf-8")
    d1 = await svc.ingest_upload("same.txt", body1, admin_id=7)
    d2 = await svc.ingest_upload("same.txt", body2, admin_id=7)
    # Same source_ref → same row, updated in place
    assert d1.id == d2.id


@pytest.mark.asyncio
async def test_ingest_upload_rejects_empty_extract(svc):
    # only-whitespace input strips to empty
    with pytest.raises(ExtractedEmpty):
        await svc.ingest_upload("blank.txt", b"   \n\t  ", admin_id=1)
