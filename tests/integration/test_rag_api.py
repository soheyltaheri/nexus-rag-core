import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_rag_query_flow_and_semantic_cache(client: AsyncClient) -> None:
    # 1. Ingest knowledge context
    doc_payload = {
        "title": "PostgreSQL Vector Search",
        "content": (
            "pgvector is an open-source vector similarity search extension for PostgreSQL. "
            "It supports exact and approximate nearest neighbor search using HNSW and IVFFlat indexes. "
            "It allows storing embeddings directly in tables alongside relational relational entities."
        ),
        "metadata": {"category": "database"},
    }
    ingest_res = await client.post("/api/v1/documents", json=doc_payload)
    assert ingest_res.status_code == 201

    # 2. Query RAG (First time: Cache Miss)
    query_payload = {
        "query": "What indexes does pgvector support for similarity search?",
        "top_k": 2,
        "enable_cache": True,
    }
    rag_res_1 = await client.post("/api/v1/rag/query", json=query_payload)
    assert rag_res_1.status_code == 200
    data_1 = rag_res_1.json()
    assert data_1["cache_hit"] is False
    assert len(data_1["sources"]) > 0
    assert "pgvector" in data_1["sources"][0]["content"]
    assert data_1["latency_ms"] > 0

    # 3. Query RAG (Second time: Cache Hit via Redis)
    rag_res_2 = await client.post("/api/v1/rag/query", json=query_payload)
    assert rag_res_2.status_code == 200
    data_2 = rag_res_2.json()
    assert data_2["cache_hit"] is True
    assert data_2["answer"] == data_1["answer"]

    # 4. Check Operational Metrics
    metrics_res = await client.get("/api/v1/metrics")
    assert metrics_res.status_code == 200
    metrics_data = metrics_res.json()
    assert metrics_data["total_documents"] >= 1
    assert metrics_data["total_vector_chunks"] >= 1
    assert metrics_data["total_queries_served"] >= 2
    assert metrics_data["cache_hits"] >= 1
