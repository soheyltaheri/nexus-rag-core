import time

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_db, get_redis
from app.core.config import settings
from app.domain.schemas.health import ComponentStatus, HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["System Health"])
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis | None = Depends(get_redis),
) -> HealthResponse:
    # 1. Check Database
    db_status = ComponentStatus(status="healthy")
    try:
        t0 = time.perf_counter()
        await db.execute(text("SELECT 1"))
        db_status.latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    except Exception as e:
        db_status.status = "unhealthy"
        db_status.error = str(e)

    # 2. Check Redis
    redis_status = ComponentStatus(status="healthy")
    if redis_client:
        try:
            t0 = time.perf_counter()
            await redis_client.ping()
            redis_status.latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        except Exception as e:
            redis_status.status = "unhealthy"
            redis_status.error = str(e)
    else:
        redis_status.status = "disconnected"
        redis_status.error = "Redis client not configured or disabled"

    overall_status = "healthy"
    if db_status.status != "healthy":
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        environment=settings.APP_ENV,
        database=db_status,
        redis=redis_status,
        version="1.0.0",
    )
