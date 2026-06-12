"""Unit tests for the token-aware Chunker."""

from app.services.chat.chunker import Chunker


def test_empty_text_returns_empty():
    chunks = Chunker(max_tokens=100, overlap_tokens=10).chunk("")
    assert chunks == []


def test_short_text_single_chunk():
    text = "Hello world. This is a short paragraph."
    chunks = Chunker(max_tokens=100, overlap_tokens=0).chunk(text)
    assert len(chunks) == 1
    assert chunks[0].index == 0
    assert chunks[0].content.strip() == text


def test_paragraph_splitting_produces_multiple_chunks():
    # ~30 tokens each, max 50 → forces split
    paras = [f"Paragraph {i}: " + "word " * 30 for i in range(4)]
    text = "\n\n".join(paras)
    chunks = Chunker(max_tokens=50, overlap_tokens=0).chunk(text)
    assert len(chunks) >= 2
    for c in chunks:
        assert c.token_count <= 60  # tolerance for overlap join


def test_chunks_have_sequential_indices():
    text = "\n\n".join(["x " * 50 for _ in range(5)])
    chunks = Chunker(max_tokens=40, overlap_tokens=5).chunk(text)
    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_overlap_present_between_chunks():
    paras = [f"para {i} " + "tok " * 40 for i in range(3)]
    text = "\n\n".join(paras)
    chunker = Chunker(max_tokens=50, overlap_tokens=10)
    chunks = chunker.chunk(text)
    if len(chunks) >= 2:
        # 2nd chunk should be longer than the raw window because of prepended overlap
        raw = chunker._pack(chunker._split_into_units(text))
        assert chunks[1].token_count >= chunker.count_tokens(raw[1])


def test_oversize_paragraph_splits_into_sentences():
    # one paragraph far larger than max_tokens — must fall back to sentence split
    para = ". ".join([f"Sentence {i}" + " word" * 10 for i in range(20)]) + "."
    chunks = Chunker(max_tokens=30, overlap_tokens=0).chunk(para)
    assert len(chunks) >= 2
    assert all(c.token_count <= 60 for c in chunks)


def test_blob_without_boundaries_is_hard_split():
    # No blank lines, no sentence terminators (e.g. a PDF table/numeric chart):
    # paragraph + sentence splitting can't help, so the chunker must hard-split
    # at the token level. Every chunk must stay within max_tokens.
    blob = "word " * 5000  # ~5000 tokens, one run, no '.', '!', '?'
    max_tokens = 100
    chunks = Chunker(max_tokens=max_tokens, overlap_tokens=0).chunk(blob)
    assert len(chunks) >= 2
    assert all(c.token_count <= max_tokens for c in chunks)


def test_no_chunk_exceeds_embedding_input_cap():
    # Regression: a single giant unit must never be emitted whole — it would
    # blow past the embedding model's per-input token limit (the 400 bug).
    blob = "1234567890" * 4000  # large run with no usable boundaries
    chunker = Chunker(max_tokens=500, overlap_tokens=50)
    # window (≤max_tokens) + prepended overlap (≤overlap_tokens); +16 tolerance
    # for tokenizer drift when the overlap tail is re-encoded at the join.
    cap = chunker.max_tokens + chunker.overlap_tokens + 16
    for c in chunker.chunk(blob):
        assert c.token_count <= cap
