import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_password_complexity_validation(client: AsyncClient):
    # Weak password without special char or uppercase should fail validation
    payload = {
        "email": "test@physioverse.app",
        "password": "weak",
        "first_name": "Test",
        "last_name": "User",
        "role": "patient",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422  # Unprocessable Entity for Pydantic validation failure


@pytest.mark.asyncio
async def test_successful_registration_and_login(client: AsyncClient):
    payload = {
        "email": "dr.smith@physioverse.app",
        "password": "StrongPassword123!",
        "first_name": "John",
        "last_name": "Smith",
        "role": "physiotherapist",
    }
    reg_response = await client.post("/api/v1/auth/register", json=payload)
    assert reg_response.status_code == 201
    assert reg_response.json()["success"] is True

    # Login
    login_payload = {
        "email": "dr.smith@physioverse.app",
        "password": "StrongPassword123!",
    }
    login_response = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_response.status_code == 200
    token_data = login_response.json()["data"]
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["role"] == "physiotherapist"
