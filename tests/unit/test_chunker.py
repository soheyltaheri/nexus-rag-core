from app.application.services.document_service import (
    compute_sha256,
    recursive_character_chunker,
)


def test_compute_sha256() -> None:
    text = "Enterprise RAG Architecture"
    h1 = compute_sha256(text)
    h2 = compute_sha256(text)
    assert len(h1) == 64
    assert h1 == h2
    assert h1 != compute_sha256("Different Text")


def test_recursive_character_chunker_empty() -> None:
    assert recursive_character_chunker("") == []
    assert recursive_character_chunker("   ") == []


def test_recursive_character_chunker_single_chunk() -> None:
    text = "Short sentence fitting in one chunk."
    chunks = recursive_character_chunker(text, chunk_size=200, chunk_overlap=20)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_recursive_character_chunker_multiple_chunks_with_overlap() -> None:
    words = [f"word{i}" for i in range(100)]
    text = " ".join(words)
    chunks = recursive_character_chunker(text, chunk_size=100, chunk_overlap=30)

    assert len(chunks) > 1
    # Check that overlap exists: some words in end of chunk 0 appear in start of chunk 1
    last_word_chunk_0 = chunks[0].split()[-1]
    assert last_word_chunk_0 in chunks[1]
