import pytest
from httpx import AsyncClient

from app.models.user import User


async def _get_token(client: AsyncClient, phone: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"phone": phone, "password": password},
    )
    return resp.json()["access_token"]


async def _create_record(client: AsyncClient, token: str, diagnosis: str, poultry_type: str = "鸡"):
    return await client.post(
        "/api/v1/records",
        json={
            "visit_date": "2024-01-15",
            "poultry_type": poultry_type,
            "record_json": {"primary_diagnosis": diagnosis},
        },
        headers={"Authorization": f"Bearer {token}"},
    )


@pytest.mark.asyncio
async def test_search_by_keyword(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")

    # Create records with different diagnoses
    await _create_record(client, token, "新城疫")
    await _create_record(client, token, "禽流感")
    await _create_record(client, token, "球虫病")

    # Search for "新城疫"
    response = await client.get(
        "/api/v1/search?keyword=新城疫",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    # All results should contain the keyword
    for item in data["items"]:
        assert "新城疫" in str(item)


@pytest.mark.asyncio
async def test_search_no_results(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")

    response = await client.get(
        "/api/v1/search?keyword=完全不存在的关键词xyz",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_search_excludes_deleted(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")

    # Create and delete a record
    resp = await _create_record(client, token, "被删除的特殊疾病XYZ")
    record_id = resp.json()["id"]
    await client.delete(
        f"/api/v1/records/{record_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Search should not find deleted records
    response = await client.get(
        "/api/v1/search?keyword=特殊疾病XYZ",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_search_with_filter(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")

    await _create_record(client, token, "鸭瘟", poultry_type="鸭")
    await _create_record(client, token, "鸭瘟疫苗", poultry_type="鸡")

    # Search with poultry_type filter
    response = await client.get(
        "/api/v1/search?keyword=鸭瘟&poultry_type=鸭",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    for item in response.json()["items"]:
        assert item["poultry_type"] == "鸭"


@pytest.mark.asyncio
async def test_search_requires_keyword(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")

    response = await client.get(
        "/api/v1/search",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422  # Missing required param
