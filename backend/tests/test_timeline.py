import pytest
from httpx import AsyncClient

from app.models.user import User


async def _get_token(client: AsyncClient, phone: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"phone": phone, "password": password},
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_timeline_basic(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")

    # Create a record
    resp = await client.post(
        "/api/v1/records",
        json={
            "visit_date": "2024-01-15",
            "poultry_type": "鸡",
            "record_json": {"primary_diagnosis": "新城疫"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    record_id = resp.json()["id"]

    # Get timeline
    response = await client.get(
        f"/api/v1/records/{record_id}/timeline",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    assert len(events) >= 1
    # First event should be creation
    assert events[0]["type"] == "create"
    assert events[0]["version"] == "1.0"


@pytest.mark.asyncio
async def test_timeline_with_updates(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")

    # Create and update
    resp = await client.post(
        "/api/v1/records",
        json={
            "visit_date": "2024-01-15",
            "poultry_type": "鸡",
            "record_json": {"primary_diagnosis": "新城疫"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    record_id = resp.json()["id"]

    await client.put(
        f"/api/v1/records/{record_id}",
        json={"record_json": {"primary_diagnosis": "新城疫(确诊)", "severity": "severe"}},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Get timeline — should have create + update
    response = await client.get(
        f"/api/v1/records/{record_id}/timeline",
        headers={"Authorization": f"Bearer {token}"},
    )
    events = response.json()
    assert len(events) >= 2
    types = [e["type"] for e in events]
    assert "create" in types
    assert "update" in types


@pytest.mark.asyncio
async def test_timeline_with_rollback(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")

    resp = await client.post(
        "/api/v1/records",
        json={
            "visit_date": "2024-01-15",
            "poultry_type": "鸡",
            "record_json": {"primary_diagnosis": "新城疫"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    record_id = resp.json()["id"]

    # Update then rollback
    await client.put(
        f"/api/v1/records/{record_id}",
        json={"record_json": {"primary_diagnosis": "修改后"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        f"/api/v1/records/{record_id}/versions/1.0/rollback",
        headers={"Authorization": f"Bearer {token}"},
    )

    response = await client.get(
        f"/api/v1/records/{record_id}/timeline",
        headers={"Authorization": f"Bearer {token}"},
    )
    events = response.json()
    types = [e["type"] for e in events]
    assert "rollback" in types
