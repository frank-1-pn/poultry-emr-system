import pytest
from httpx import AsyncClient

from app.models.user import User


async def _get_token(client: AsyncClient, phone: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"phone": phone, "password": password},
    )
    return resp.json()["access_token"]


async def _create_record(client: AsyncClient, token: str) -> str:
    resp = await client.post(
        "/api/v1/records",
        json={
            "visit_date": "2024-01-15",
            "poultry_type": "鸡",
            "breed": "蛋鸡",
            "age_days": 120,
            "affected_count": 30,
            "total_flock": 500,
            "record_json": {
                "basic_info": {"species": "蛋鸡", "age_days": 120},
                "symptoms": ["精神萎靡", "采食下降"],
                "primary_diagnosis": "新城疫",
                "severity": "severe",
                "treatment": {"drug": "疫苗", "method": "饮水免疫"},
                "notes": "建议隔离",
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_export_pdf(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")
    record_id = await _create_record(client, token)

    response = await client.get(
        f"/api/v1/export/records/{record_id}/pdf",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    # PDF starts with %PDF
    assert response.content[:5] == b"%PDF-"


@pytest.mark.asyncio
async def test_export_word(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")
    record_id = await _create_record(client, token)

    response = await client.get(
        f"/api/v1/export/records/{record_id}/word",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "wordprocessingml" in response.headers["content-type"]
    # DOCX is a ZIP file, starts with PK
    assert response.content[:2] == b"PK"


@pytest.mark.asyncio
async def test_export_excel(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")
    await _create_record(client, token)
    await _create_record(client, token)

    response = await client.get(
        "/api/v1/export/records/excel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "spreadsheetml" in response.headers["content-type"]
    # XLSX is a ZIP file
    assert response.content[:2] == b"PK"
