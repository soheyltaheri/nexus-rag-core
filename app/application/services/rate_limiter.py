import logging
import time

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)


class SlidingWindowRateLimiter:
    """Distributed rate limiter backed by Redis."""

    def __init__(self, redis_client: aioredis.Redis | None) -> None:
        self.redis = redis_client
        self.limit = settings.RATE_LIMIT_REQUESTS_PER_MINUTE
        self.window_seconds = 60

    async def is_allowed(self, client_identifier: str) -> tuple[bool, int]:
        """Check if request is allowed under current sliding window.

        Returns (is_allowed, remaining_requests).
        """
        if not self.redis:
            # Allow by default if Redis is not active
            return True, self.limit

        key = f"ratelimit:{client_identifier}"
        now = time.time()
        window_start = now - self.window_seconds

        try:
            pipe = self.redis.pipeline()
            # Remove timestamps older than window
            pipe.zremrangebyscore(key, 0, window_start)
            # Add current timestamp
            pipe.zadd(key, {str(now): now})
            # Count elements in window
            pipe.zcard(key)
            # Set key expiry
            pipe.expire(key, self.window_seconds)
            results = await pipe.execute()

            request_count = results[2]
            remaining = max(0, self.limit - request_count)
            return request_count <= self.limit, remaining
        except Exception as e:
            logger.warning(f"Rate limiter check failed: {e}")
            return True, self.limit
