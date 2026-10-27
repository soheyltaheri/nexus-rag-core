import pytest

from app.application.services.cache_service import SemanticCacheService
from tests.conftest import MockRedis


@pytest.mark.asyncio
async def test_semantic_cache_set_and_get() -> None:
    mock_redis = MockRedis()
    cache_service = SemanticCacheService(redis_client=mock_redis)  # type: ignore

    query = "What is Clean Architecture?"
    answer = "Clean Architecture is a software design philosophy..."
    sources = [{"chunk_id": "c1", "document_id": "d1", "content": "Clean arch...", "score": 0.95}]

    # Initially cache should be empty
    cached = await cache_service.get(query)
    assert cached is None

    # Store in cache
    await cache_service.set(query=query, answer=answer, sources=sources)

    # Now retrieve
    retrieved = await cache_service.get(query)
    assert retrieved is not None
    assert retrieved["answer"] == answer
    assert len(retrieved["sources"]) == 1
    assert retrieved["sources"][0]["chunk_id"] == "c1"


@pytest.mark.asyncio
async def test_semantic_cache_without_redis() -> None:
    cache_service = SemanticCacheService(redis_client=None)
    assert await cache_service.get("any query") is None
    # set should not raise exception
    await cache_service.set("any query", "answer", [])
