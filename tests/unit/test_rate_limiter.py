import pytest

from app.application.services.rate_limiter import SlidingWindowRateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_without_redis() -> None:
    limiter = SlidingWindowRateLimiter(redis_client=None)
    allowed, remaining = await limiter.is_allowed("test-client")
    assert allowed is True
    assert remaining == limiter.limit
