import hashlib
import json
import logging
from typing import Any, cast

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)


class SemanticCacheService:
    def __init__(self, redis_client: aioredis.Redis | None) -> None:
        self.redis = redis_client
        self.ttl = settings.SEMANTIC_CACHE_TTL_SECONDS

    def _hash_key(self, query: str, document_id: str | None = None) -> str:
        normalized = query.strip().lower()
        key_raw = f"{document_id or 'all'}:{normalized}"
        return f"rag:cache:{hashlib.sha256(key_raw.encode('utf-8')).hexdigest()}"

    async def get(self, query: str, document_id: str | None = None) -> dict[str, Any] | None:
        """Retrieve cached response if available in Redis."""
        if not self.redis:
            return None

        try:
            cache_key = self._hash_key(query, document_id)
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                logger.info(f"Semantic cache hit for query: '{query}'")
                return cast(dict[str, Any], json.loads(cached_data))
        except Exception as e:
            logger.warning(f"Semantic cache read failed: {e}")
        return None

    async def set(
        self,
        query: str,
        answer: str,
        sources: list[dict[str, Any]],
        document_id: str | None = None,
    ) -> None:
        """Store query response and metadata in Redis with TTL."""
        if not self.redis:
            return

        try:
            cache_key = self._hash_key(query, document_id)
            payload = {
                "answer": answer,
                "sources": sources,
                "cached_at": settings.APP_NAME,
            }
            await self.redis.set(cache_key, json.dumps(payload), ex=self.ttl)
            logger.info(f"Cached response for query: '{query}' (TTL: {self.ttl}s)")
        except Exception as e:
            logger.warning(f"Semantic cache write failed: {e}")
