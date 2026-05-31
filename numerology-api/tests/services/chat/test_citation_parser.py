"""Unit tests for citation parser."""

from app.schemas.chat.retrieval import RetrievedChunk
from app.services.chat.citation_parser import build_citations, extract_used_indices


def _chunks(n: int) -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            chunk_id=100 + i,
            document_id=10 + i,
            source_type="numerology:mission_number",
            source_ref=f"MN_{i}",
            title=f"Title {i}",
            content=f"content {i}",
            score=0.9 - 0.05 * i,
        )
        for i in range(1, n + 1)
    ]


def test_extract_used_indices_in_order_of_first_appearance():
    text = "Per [2], the meaning is X [1]. As also noted in [2] again, X."
    assert extract_used_indices(text) == [2, 1]


def test_extract_empty_when_no_markers():
    assert extract_used_indices("nothing here") == []
    assert extract_used_indices("") == []


def test_build_citations_maps_indices_to_chunks():
    chunks = _chunks(3)
    text = "Answer [1] then [3]."
    cites = build_citations(text, chunks)
    assert [c.index for c in cites] == [1, 3]
    assert cites[0].chunk_id == 101  # 1-indexed → chunks[0]
    assert cites[1].chunk_id == 103
    assert cites[0].source_ref == "MN_1"


def test_build_citations_drops_out_of_range_index():
    chunks = _chunks(2)
    text = "Hallucinated [9] reference."
    assert build_citations(text, chunks) == []


def test_build_citations_dedup_repeated_marker():
    chunks = _chunks(2)
    text = "See [1]. As [1] said, ..."
    cites = build_citations(text, chunks)
    assert len(cites) == 1
    assert cites[0].chunk_id == 101
