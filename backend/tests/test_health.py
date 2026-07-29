import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "healthy")
    assert data["message"] == "Server is running"


@pytest.mark.asyncio
async def test_security_headers(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    if "X-Frame-Options" in response.headers:
        assert response.headers.get("X-Frame-Options") == "DENY"
