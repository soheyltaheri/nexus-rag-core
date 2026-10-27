import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_document_ingestion_and_retrieval(client: AsyncClient) -> None:
    # 1. Ingest Document
    payload = {
        "title": "Clean Architecture Principles",
        "content": (
            "Clean Architecture separates domain logic from delivery mechanisms. "
            "Entities encapsulate enterprise business rules. "
            "Use cases orchestrate data flow to and from entities. "
            "FastAPI serves as the driving adapter while Postgres and Redis act as driven adapters."
        ),
        "metadata": {"author": "Uncle Bob", "domain": "software_architecture"},
    }

    create_res = await client.post("/api/v1/documents", json=payload)
    assert create_res.status_code == 201
    doc_data = create_res.json()
    assert doc_data["title"] == payload["title"]
    assert doc_data["chunk_count"] > 0
    assert doc_data["status"] == "indexed"
    doc_id = doc_data["id"]

    # 2. Get Document by ID
    get_res = await client.get(f"/api/v1/documents/{doc_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == doc_id

    # 3. List Documents
    list_res = await client.get("/api/v1/documents")
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) >= 1
    assert any(item["id"] == doc_id for item in items)


@pytest.mark.asyncio
async def test_get_nonexistent_document_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/documents/non-existent-uuid")
    assert response.status_code == 404
