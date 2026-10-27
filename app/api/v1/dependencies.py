from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.cache_service import SemanticCacheService
from app.application.services.document_service import DocumentService
from app.application.services.rag_service import RAGService
from app.application.services.rate_limiter import SlidingWindowRateLimiter
from app.infrastructure.database import get_db_session
from app.infrastructure.llm_provider import LLMProviderInterface, OpenAILLMProvider
from app.infrastructure.redis import get_redis_client
from app.infrastructure.vector_store import PgVectorStore, VectorStoreInterface

# Singletons for providers
_vector_store = PgVectorStore()
_llm_provider = OpenAILLMProvider()


def get_db() -> AsyncGenerator[AsyncSession, None]:
    return get_db_session()


def get_redis() -> aioredis.Redis | None:
    try:
        return get_redis_client()
    except Exception:
        return None


def get_vector_store() -> VectorStoreInterface:
    return _vector_store


def get_llm_provider() -> LLMProviderInterface:
    return _llm_provider


def get_cache_service(
    redis_client: aioredis.Redis | None = Depends(get_redis),
) -> SemanticCacheService:
    return SemanticCacheService(redis_client=redis_client)


def get_document_service(
    vector_store: VectorStoreInterface = Depends(get_vector_store),
    llm_provider: LLMProviderInterface = Depends(get_llm_provider),
) -> DocumentService:
    return DocumentService(vector_store=vector_store, llm_provider=llm_provider)


def get_rag_service(
    vector_store: VectorStoreInterface = Depends(get_vector_store),
    llm_provider: LLMProviderInterface = Depends(get_llm_provider),
    cache_service: SemanticCacheService = Depends(get_cache_service),
) -> RAGService:
    return RAGService(
        vector_store=vector_store,
        llm_provider=llm_provider,
        cache_service=cache_service,
    )


async def check_rate_limit(
    x_forwarded_for: str | None = Header(default=None),
    redis_client: aioredis.Redis | None = Depends(get_redis),
) -> None:
    client_id = x_forwarded_for or "anonymous_client"
    limiter = SlidingWindowRateLimiter(redis_client=redis_client)
    is_allowed, remaining = await limiter.is_allowed(client_id)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait before retrying.",
            headers={"Retry-After": "60"},
        )
