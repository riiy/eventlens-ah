import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_create_document(client: AsyncClient):
    response = await client.post("/api/raw-documents/", json={
        "source": "test_source",
        "title": "Test Document",
        "content": "This is a test document with sufficient content for testing deduplication.",
        "language": "en",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["source"] == "test_source"
    assert data["title"] == "Test Document"
    assert "id" in data
    assert "content_hash" in data


@pytest.mark.asyncio
async def test_list_documents(client: AsyncClient):
    response = await client.get("/api/raw-documents/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_document_deduplication(client: AsyncClient):
    payload = {
        "source": "test_source",
        "title": "Duplicate Test",
        "content": "This content should be deduplicated.",
        "language": "en",
    }
    r1 = await client.post("/api/raw-documents/", json=payload)
    r2 = await client.post("/api/raw-documents/", json=payload)
    assert r1.status_code == 201
    assert r2.status_code == 201
    # Same content should produce same content_hash and return existing doc
    assert r1.json()["content_hash"] == r2.json()["content_hash"]


@pytest.mark.asyncio
async def test_get_document_not_found(client: AsyncClient):
    response = await client.get("/api/raw-documents/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_dashboard_summary(client: AsyncClient):
    response = await client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data
    assert "total_events" in data
    assert "event_type_distribution" in data


@pytest.mark.asyncio
async def test_list_events(client: AsyncClient):
    response = await client.get("/api/events/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_assets(client: AsyncClient):
    response = await client.get("/api/assets/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_create_asset(client: AsyncClient):
    response = await client.post("/api/assets/", json={
        "symbol": "TEST.SH",
        "name": "Test Asset",
        "market": "A_SHARE",
        "exchange": "SSE",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["symbol"] == "TEST.SH"


@pytest.mark.asyncio
async def test_run_demo_ingestion(client: AsyncClient):
    response = await client.post("/api/ingestion/run-demo")
    assert response.status_code == 200
    data = response.json()
    assert data["documents_ingested"] > 0
    assert data["events_extracted"] > 0
    assert "message" in data