import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.chunk import Chunk
from app.domain.models.document import Document
from app.infrastructure.vector_store import PgVectorStore, cosine_similarity


def test_cosine_similarity_identical() -> None:
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    sim = cosine_similarity(v1, v2)
    assert abs(sim - 1.0) < 1e-5


def test_cosine_similarity_orthogonal() -> None:
    v1 = [1.0, 0.0, 0.0]
    v2 = [0.0, 1.0, 0.0]
    sim = cosine_similarity(v1, v2)
    assert abs(sim - 0.0) < 1e-5


def test_cosine_similarity_zero_vector() -> None:
    v1 = [0.0, 0.0, 0.0]
    v2 = [1.0, 2.0, 3.0]
    assert cosine_similarity(v1, v2) == 0.0


@pytest.mark.asyncio
async def test_vector_store_add_and_search(db_session: AsyncSession) -> None:
    store = PgVectorStore()
    doc = Document(title="Test Vector Search", content_hash="hash1", metadata_json={})
    db_session.add(doc)
    await db_session.flush()

    c1 = Chunk(
        document_id=doc.id,
        chunk_index=0,
        content="PostgreSQL pgvector rocks",
        embedding=[1.0, 0.0, 0.0],
    )
    c2 = Chunk(
        document_id=doc.id,
        chunk_index=1,
        content="Irrelevant text content",
        embedding=[0.0, 1.0, 0.0],
    )
    await store.add_chunks(db_session, [c1, c2])

    results = await store.similarity_search(
        session=db_session,
        query_vector=[0.9, 0.1, 0.0],
        top_k=2,
    )
    assert len(results) == 2
    assert results[0][0].id == c1.id
    assert results[0][1] > results[1][1]
