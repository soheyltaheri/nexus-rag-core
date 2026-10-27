import logging
import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.cache_service import SemanticCacheService
from app.core.config import settings
from app.domain.models.query_log import QueryLog
from app.domain.schemas.rag import RAGQueryRequest, RAGQueryResponse, RAGSource
from app.infrastructure.llm_provider import LLMProviderInterface
from app.infrastructure.vector_store import VectorStoreInterface

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(
        self,
        vector_store: VectorStoreInterface,
        llm_provider: LLMProviderInterface,
        cache_service: SemanticCacheService,
    ) -> None:
        self.vector_store = vector_store
        self.llm_provider = llm_provider
        self.cache = cache_service

    async def execute_query(
        self,
        session: AsyncSession,
        req: RAGQueryRequest,
    ) -> RAGQueryResponse:
        start_time = time.perf_counter()

        # 1. Semantic Cache Lookup
        if req.enable_cache:
            cached_data = await self.cache.get(req.query, req.document_id)
            if cached_data:
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                cached_sources = [RAGSource(**s) for s in cached_data.get("sources", [])]

                # Asynchronously record query log
                log_entry = QueryLog(
                    query_text=req.query,
                    cache_hit=True,
                    latency_ms=round(latency_ms, 2),
                    tokens_used=0,
                )
                session.add(log_entry)
                await session.flush()

                return RAGQueryResponse(
                    query=req.query,
                    answer=cached_data["answer"],
                    sources=cached_sources,
                    cache_hit=True,
                    latency_ms=round(latency_ms, 2),
                    model=settings.OPENAI_MODEL,
                )

        # 2. Dense Query Embedding
        query_vector = await self.llm_provider.get_embedding(req.query)

        # 3. Vector Similarity Search
        scored_chunks = await self.vector_store.similarity_search(
            session=session,
            query_vector=query_vector,
            top_k=req.top_k,
            document_id=req.document_id,
        )

        sources: list[RAGSource] = [
            RAGSource(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                content=chunk.content,
                score=round(score, 4),
            )
            for chunk, score in scored_chunks
        ]

        # 4. Context Synthesis & Prompt Construction
        context_parts = [
            f"[Source {idx + 1} | Score: {src.score}]: {src.content}"
            for idx, src in enumerate(sources)
        ]
        context_text = "\n\n".join(context_parts) if context_parts else "No relevant context found."

        # 5. LLM Completion
        answer = await self.llm_provider.generate(prompt=req.query, context=context_text)

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # 6. Save to Semantic Cache
        if req.enable_cache and sources:
            serialized_sources = [s.model_dump() for s in sources]
            await self.cache.set(
                query=req.query,
                answer=answer,
                sources=serialized_sources,
                document_id=req.document_id,
            )

        # 7. Persist Query Log
        log_entry = QueryLog(
            query_text=req.query,
            cache_hit=False,
            latency_ms=round(latency_ms, 2),
            tokens_used=len(answer.split()) + len(context_text.split()),
        )
        session.add(log_entry)
        await session.flush()

        return RAGQueryResponse(
            query=req.query,
            answer=answer,
            sources=sources,
            cache_hit=False,
            latency_ms=round(latency_ms, 2),
            model=settings.OPENAI_MODEL,
        )
