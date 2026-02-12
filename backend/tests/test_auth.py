import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "newvet",
            "phone": "13900000001",
            "password": "password123",
            "full_name": "New Vet",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newvet"
    assert data["role"] == "veterinarian"
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_register_duplicate_phone(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "vet1",
            "phone": "13900000099",
            "password": "password123",
            "full_name": "Vet 1",
        },
    )
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "vet2",
            "phone": "13900000099",
            "password": "password123",
            "full_name": "Vet 2",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login(client: AsyncClient, vet_user: User):
    response = await client.post(
        "/api/v1/auth/login",
        json={"phone": "13800000002", "password": "vet123456"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, vet_user: User):
    response = await client.post(
        "/api/v1/auth/login",
        json={"phone": "13800000002", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, vet_user: User):
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"phone": "13800000002", "password": "vet123456"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_me(client: AsyncClient, vet_user: User):
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"phone": "13800000002", "password": "vet123456"},
    )
    token = login_resp.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["phone"] == "13800000002"
