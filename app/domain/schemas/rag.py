from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Natural language search or question")
    top_k: int = Field(default=3, ge=1, le=20, description="Number of context chunks to retrieve")
    document_id: str | None = Field(default=None, description="Optional document filter")
    enable_cache: bool = Field(default=True, description="Enable Redis semantic caching")


class RAGSource(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float


class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[RAGSource]
    cache_hit: bool
    latency_ms: float
    model: str
