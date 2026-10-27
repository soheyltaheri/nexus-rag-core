from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_db
from app.domain.models.chunk import Chunk
from app.domain.models.document import Document
from app.domain.models.query_log import QueryLog

router = APIRouter(prefix="/metrics", tags=["Operational Metrics"])


@router.get("", response_model=dict[str, Any])
async def get_system_metrics(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Retrieve operational telemetry and vector index statistics."""
    # 1. Total documents
    doc_count_res = await db.execute(select(func.count(Document.id)))
    total_docs = doc_count_res.scalar_one() or 0

    # 2. Total chunks indexed
    chunk_count_res = await db.execute(select(func.count(Chunk.id)))
    total_chunks = chunk_count_res.scalar_one() or 0

    # 3. Query logs summary
    total_queries_res = await db.execute(select(func.count(QueryLog.id)))
    total_queries = total_queries_res.scalar_one() or 0

    cache_hits_res = await db.execute(
        select(func.count(QueryLog.id)).where(QueryLog.cache_hit.is_(True))
    )
    cache_hits = cache_hits_res.scalar_one() or 0

    avg_latency_res = await db.execute(select(func.avg(QueryLog.latency_ms)))
    avg_latency = avg_latency_res.scalar_one() or 0.0

    cache_hit_rate = (cache_hits / total_queries * 100.0) if total_queries > 0 else 0.0

    return {
        "total_documents": total_docs,
        "total_vector_chunks": total_chunks,
        "total_queries_served": total_queries,
        "cache_hits": cache_hits,
        "cache_hit_rate_pct": round(cache_hit_rate, 2),
        "avg_query_latency_ms": round(float(avg_latency), 2),
    }
