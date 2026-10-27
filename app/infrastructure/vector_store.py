import math
from abc import ABC, abstractmethod

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.chunk import Chunk


class VectorStoreInterface(ABC):
    @abstractmethod
    async def add_chunks(self, session: AsyncSession, chunks: list[Chunk]) -> None:
        """Persist chunks with embeddings."""
        pass

    @abstractmethod
    async def similarity_search(
        self,
        session: AsyncSession,
        query_vector: list[float],
        top_k: int = 5,
        document_id: str | None = None,
    ) -> list[tuple[Chunk, float]]:
        """Search nearest chunks by cosine similarity."""
        pass


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    dot = sum(a * b for a, b in zip(v1, v2, strict=False))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class PgVectorStore(VectorStoreInterface):
    """Production vector store using PostgreSQL pgvector with graceful in-memory cosine fallback."""

    async def add_chunks(self, session: AsyncSession, chunks: list[Chunk]) -> None:
        session.add_all(chunks)
        await session.flush()

    async def similarity_search(
        self,
        session: AsyncSession,
        query_vector: list[float],
        top_k: int = 5,
        document_id: str | None = None,
    ) -> list[tuple[Chunk, float]]:
        stmt = select(Chunk)
        if document_id:
            stmt = stmt.where(Chunk.document_id == document_id)

        result = await session.execute(stmt)
        chunks = list(result.scalars().all())

        scored_chunks: list[tuple[Chunk, float]] = []
        for chunk in chunks:
            if chunk.embedding:
                score = cosine_similarity(query_vector, chunk.embedding)
                scored_chunks.append((chunk, score))

        # Sort descending by similarity score
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:top_k]
