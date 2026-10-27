import logging

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: aioredis.Redis | None = None


def get_redis_client() -> aioredis.Redis:
    """Singleton getter for async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2.0,
            socket_timeout=2.0,
        )
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection pool."""
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.close()
        except Exception as e:
            logger.warning(f"Error closing redis client: {e}")
        _redis_client = None


async def ping_redis() -> bool:
    """Health check for Redis connectivity."""
    try:
        client = get_redis_client()
        return bool(await client.ping())
    except Exception as e:
        logger.warning(f"Redis ping failed: {e}")
        return False
