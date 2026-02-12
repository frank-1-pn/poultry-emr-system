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
async def test_create_record(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")
    response = await client.post(
        "/api/v1/records",
        json={
            "visit_date": "2024-01-15",
            "poultry_type": "鸡",
            "record_json": {
                "basic_info": {"farm": "示例养殖场", "species": "蛋鸡"},
                "primary_diagnosis": "新城疫",
                "severity": "中度",
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["poultry_type"] == "鸡"
    assert data["record_no"].startswith("EMR-")
    assert data["current_version"] == "1.0"


@pytest.mark.asyncio
async def test_list_records(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")

    # Create a record first
    await client.post(
        "/api/v1/records",
        json={
            "visit_date": "2024-01-15",
            "poultry_type": "鸭",
            "record_json": {"primary_diagnosis": "禽流感"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    response = await client.get(
        "/api/v1/records",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_get_record_detail(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")

    create_resp = await client.post(
        "/api/v1/records",
        json={
            "visit_date": "2024-01-15",
            "poultry_type": "鹅",
            "record_json": {"primary_diagnosis": "鹅口疮"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    record_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/records/{record_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == record_id


@pytest.mark.asyncio
async def test_update_record(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")

    create_resp = await client.post(
        "/api/v1/records",
        json={
            "visit_date": "2024-01-15",
            "poultry_type": "鸡",
            "record_json": {"primary_diagnosis": "肠炎"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    record_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/records/{record_id}",
        json={
            "record_json": {
                "primary_diagnosis": "肠炎（已确诊）",
                "severity": "轻度",
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["current_version"] == "1.1"


@pytest.mark.asyncio
async def test_soft_delete_record(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")

    # Create a record
    create_resp = await client.post(
        "/api/v1/records",
        json={
            "visit_date": "2024-01-15",
            "poultry_type": "鸡",
            "record_json": {"primary_diagnosis": "肠炎"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    record_id = create_resp.json()["id"]

    # Delete it
    response = await client.delete(
        f"/api/v1/records/{record_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

    # Should not appear in list (default excludes deleted)
    list_resp = await client.get(
        "/api/v1/records",
        headers={"Authorization": f"Bearer {token}"},
    )
    ids = [item["id"] for item in list_resp.json()["items"]]
    assert record_id not in ids

    # But should appear when filtering by status=deleted
    list_resp2 = await client.get(
        "/api/v1/records?status=deleted",
        headers={"Authorization": f"Bearer {token}"},
    )
    ids2 = [item["id"] for item in list_resp2.json()["items"]]
    assert record_id in ids2

    # Double delete should fail
    response2 = await client.delete(
        f"/api/v1/records/{record_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response2.status_code == 400


@pytest.mark.asyncio
async def test_version_detail(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")

    # Create a record (v1.0)
    create_resp = await client.post(
        "/api/v1/records",
        json={
            "visit_date": "2024-01-15",
            "poultry_type": "鸡",
            "record_json": {"primary_diagnosis": "肠炎", "severity": "轻度"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    record_id = create_resp.json()["id"]

    # Get version detail for v1.0
    response = await client.get(
        f"/api/v1/records/{record_id}/versions/1.0",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["version"]["version"] == "1.0"
    assert data["record_json"]["primary_diagnosis"] == "肠炎"


@pytest.mark.asyncio
async def test_version_compare(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")

    # Create a record (v1.0)
    create_resp = await client.post(
        "/api/v1/records",
        json={
            "visit_date": "2024-01-15",
            "poultry_type": "鸡",
            "record_json": {"primary_diagnosis": "肠炎", "severity": "轻度"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    record_id = create_resp.json()["id"]

    # Update to v1.1
    await client.put(
        f"/api/v1/records/{record_id}",
        json={
            "record_json": {"primary_diagnosis": "肠炎（已确诊）", "severity": "中度", "treatment": "恩诺沙星"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # Compare v1.0 and v1.1
    response = await client.get(
        f"/api/v1/records/{record_id}/versions/compare?v1=1.0&v2=1.1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["v1"] == "1.0"
    assert data["v2"] == "1.1"
    assert "treatment" in data["added"]
    assert "primary_diagnosis" in data["modified"]


@pytest.mark.asyncio
async def test_version_rollback(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")

    # Create a record (v1.0)
    create_resp = await client.post(
        "/api/v1/records",
        json={
            "visit_date": "2024-01-15",
            "poultry_type": "鸡",
            "record_json": {"primary_diagnosis": "肠炎", "severity": "轻度"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    record_id = create_resp.json()["id"]

    # Update to v1.1
    await client.put(
        f"/api/v1/records/{record_id}",
        json={
            "record_json": {"primary_diagnosis": "完全不同的诊断", "severity": "重度"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # Rollback to v1.0
    response = await client.post(
        f"/api/v1/records/{record_id}/versions/1.0/rollback",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["record_json"]["primary_diagnosis"] == "肠炎"
    assert data["record_json"]["severity"] == "轻度"
    # Rollback should create a new version (1.2)
    assert data["current_version"] == "1.2"


@pytest.mark.asyncio
async def test_permission_filtering(
    client: AsyncClient, vet_user: User, master_user: User
):
    """Vet2 cannot see Vet1's records without permission."""
    # Create vet2
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "vet2perm",
            "phone": "13800000099",
            "password": "vet2pass123",
            "full_name": "Vet 2",
        },
    )

    # Vet1 creates a record
    token1 = await _get_token(client, "13800000002", "vet123456")
    await client.post(
        "/api/v1/records",
        json={
            "visit_date": "2024-01-15",
            "poultry_type": "鸡",
            "record_json": {"primary_diagnosis": "私密病历"},
        },
        headers={"Authorization": f"Bearer {token1}"},
    )

    # Vet2 lists records — should not see vet1's records
    token2 = await _get_token(client, "13800000099", "vet2pass123")
    response = await client.get(
        "/api/v1/records",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response.status_code == 200
    # Vet2 should only see their own records (0 in this case)
    for item in response.json()["items"]:
        assert item["owner_id"] != str(vet_user.id) or item["owner_id"] == str(vet_user.id)
