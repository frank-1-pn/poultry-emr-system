import pytest
from httpx import AsyncClient

from app.models.user import User


async def _get_token(client: AsyncClient, phone: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"phone": phone, "password": password},
    )
    return resp.json()["access_token"]


async def _create_record(client: AsyncClient, token: str, diagnosis: str, severity: str = "moderate"):
    return await client.post(
        "/api/v1/records",
        json={
            "visit_date": "2024-01-15",
            "poultry_type": "鸡",
            "record_json": {
                "primary_diagnosis": diagnosis,
                "severity": severity,
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )


@pytest.mark.asyncio
async def test_overview_requires_master(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")
    response = await client.get(
        "/api/v1/statistics/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_overview_stats(client: AsyncClient, master_user: User, vet_user: User):
    vet_token = await _get_token(client, "13800000002", "vet123456")
    await _create_record(client, vet_token, "新城疫")
    await _create_record(client, vet_token, "禽流感")

    master_token = await _get_token(client, "13800000001", "master123")
    response = await client.get(
        "/api/v1/statistics/overview",
        headers={"Authorization": f"Bearer {master_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_records"] >= 2
    assert data["total_users"] >= 2
    assert data["active_veterinarians"] >= 1


@pytest.mark.asyncio
async def test_disease_stats(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")
    await _create_record(client, token, "新城疫")
    await _create_record(client, token, "新城疫")
    await _create_record(client, token, "禽流感")

    response = await client.get(
        "/api/v1/statistics/diseases",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # 新城疫 should have count >= 2
    ncy = next((d for d in data if d["diagnosis"] == "新城疫"), None)
    assert ncy is not None
    assert ncy["count"] >= 2


@pytest.mark.asyncio
async def test_poultry_type_stats(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")
    await _create_record(client, token, "测试病")

    response = await client.get(
        "/api/v1/statistics/poultry-types",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_severity_stats(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")
    await _create_record(client, token, "轻病", severity="mild")
    await _create_record(client, token, "重病", severity="severe")

    response = await client.get(
        "/api/v1/statistics/severity",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_trend_stats(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")
    await _create_record(client, token, "趋势测试")

    response = await client.get(
        "/api/v1/statistics/trend",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
