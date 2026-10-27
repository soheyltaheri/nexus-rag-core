from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import (
    check_rate_limit,
    get_db,
    get_rag_service,
)
from app.application.services.rag_service import RAGService
from app.domain.schemas.rag import RAGQueryRequest, RAGQueryResponse

router = APIRouter(prefix="/rag", tags=["RAG & Semantic Retrieval"])


@router.post(
    "/query",
    response_model=RAGQueryResponse,
    dependencies=[Depends(check_rate_limit)],
)
async def query_knowledge_base(
    req: RAGQueryRequest,
    db: AsyncSession = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service),
) -> RAGQueryResponse:
    """Execute enterprise RAG search:

    1. Checks Redis Semantic Cache
    2. Runs vector similarity search on PostgreSQL pgvector
    3. Synthesizes context with LLM
    4. Caches result and returns cited sources with latency telemetry
    """
    try:
        response = await rag_service.execute_query(session=db, req=req)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG query execution failed: {e}",
        ) from e
