"""Unit tests for RetrievalService.

The pgvector cosine query is PG-only, so we mock session.execute() and the
embedding call to assert pure assembly + threshold filtering behavior.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.chat.retrieval_service import RetrievalService


class _FakeEmbeddings:
    async def embed_one(self, text: str) -> list[float]:
        return [0.1] * 768


def _row(chunk_id: int, score: float) -> dict:
    return {
        "chunk_id": chunk_id,
        "document_id": chunk_id * 10,
        "source_type": "numerology:mission_number",
        "source_ref": f"MN_{chunk_id}",
        "title": f"T{chunk_id}",
        "content": f"chunk text {chunk_id}",
        "score": score,
    }


def _session_returning(rows: list[dict]) -> MagicMock:
    """Build a MagicMock async session whose execute() returns the rows."""
    session = MagicMock()
    result = MagicMock()
    result.mappings.return_value.all.return_value = rows
    session.execute = AsyncMock(return_value=result)
    return session


@pytest.mark.asyncio
async def test_empty_query_returns_empty():
    svc = RetrievalService(_session_returning([]), _FakeEmbeddings())
    assert await svc.retrieve("   ") == []


@pytest.mark.asyncio
async def test_filters_below_threshold():
    rows = [_row(1, 0.9), _row(2, 0.7), _row(3, 0.5)]
    svc = RetrievalService(_session_returning(rows), _FakeEmbeddings())
    out = await svc.retrieve("query", top_k=5, threshold=0.6)
    assert [c.chunk_id for c in out] == [1, 2]


@pytest.mark.asyncio
async def test_all_rows_pass_when_threshold_zero():
    rows = [_row(1, 0.9), _row(2, 0.3), _row(3, 0.1)]
    svc = RetrievalService(_session_returning(rows), _FakeEmbeddings())
    out = await svc.retrieve("q", top_k=3, threshold=0.0)
    assert len(out) == 3


@pytest.mark.asyncio
async def test_passes_top_k_to_query():
    session = _session_returning([])
    svc = RetrievalService(session, _FakeEmbeddings())
    await svc.retrieve("q", top_k=7, threshold=0.6)
    _args, kwargs = session.execute.call_args
    # second positional arg is the params dict
    params = session.execute.call_args.args[1]
    assert params["k"] == 7
    # emb param is a pgvector literal string
    assert params["emb"].startswith("[") and params["emb"].endswith("]")


def test_vector_literal_format():
    assert RetrievalService._vector_literal([1.0, 0.5]).startswith("[1.00000000,0.50000000")


# ---------------------------------------------------------------------------
# Hybrid KB + user-PDF merge (Phase 03)
# ---------------------------------------------------------------------------


def _kb_row(chunk_id: int, score: float) -> dict:
    return {
        "chunk_id": chunk_id,
        "document_id": chunk_id * 10,
        "source_type": "numerology:mission_number",
        "source_ref": f"MN_{chunk_id}",
        "title": f"T{chunk_id}",
        "content": f"kb {chunk_id}",
        "score": score,
    }


def _pdf_row(chunk_id: int, score: float, page: int = 1) -> dict:
    return {
        "chunk_id": chunk_id,
        "document_id": 999,  # pdf_index_id stub
        "source_type": "user_pdf",
        "source_ref": str(page),
        "title": None,
        "content": f"pdf {chunk_id}",
        "score": score,
    }


def _session_returning_sequence(*row_batches: list[dict]) -> MagicMock:
    """Each call to session.execute() yields the next batch in sequence."""
    session = MagicMock()

    def _make_result(rows):
        r = MagicMock()
        r.mappings.return_value.all.return_value = rows
        return r

    session.execute = AsyncMock(side_effect=[_make_result(b) for b in row_batches])
    return session


@pytest.mark.asyncio
async def test_hybrid_merges_kb_and_pdf_rows_sorted_by_score():
    kb_batch = [_kb_row(1, 0.95)]  # kb_k = 1 when top_k=3
    pdf_batch = [_pdf_row(101, 0.92, page=4), _pdf_row(102, 0.88, page=5)]  # pdf_k = 2
    session = _session_returning_sequence(kb_batch, pdf_batch)
    svc = RetrievalService(session, _FakeEmbeddings())

    out = await svc.retrieve("q", top_k=3, threshold=0.6, pdf_context_id=42)
    # Two SQL calls expected (kb + pdf)
    assert session.execute.call_count == 2
    # Sorted by score desc
    assert [c.score for c in out] == [0.95, 0.92, 0.88]
    # PDF rows tagged source_type="user_pdf" with page number in source_ref
    assert out[1].source_type == "user_pdf"
    assert out[1].source_ref == "4"


@pytest.mark.asyncio
async def test_hybrid_passes_pdf_index_id_to_pdf_query():
    session = _session_returning_sequence([], [])
    svc = RetrievalService(session, _FakeEmbeddings())
    await svc.retrieve("q", top_k=4, threshold=0.6, pdf_context_id=77)
    # 2nd call is the user_pdf_chunks query
    _, kwargs = session.execute.call_args_list[1]
    params = session.execute.call_args_list[1].args[1]
    assert params["pdf_index_id"] == 77
