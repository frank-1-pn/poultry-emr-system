import pytest
from httpx import AsyncClient

from app.models.user import User
from app.services.search_config_service import init_defaults


async def _get_token(client: AsyncClient, phone: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"phone": phone, "password": password},
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_list_configs_empty(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")
    response = await client.get(
        "/api/v1/search-config",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_init_defaults_and_list(client: AsyncClient, vet_user: User, db_session):
    # Init defaults
    created = await init_defaults(db_session)
    await db_session.commit()
    assert len(created) == 3

    token = await _get_token(client, "13800000002", "vet123456")
    response = await client.get(
        "/api/v1/search-config",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    configs = response.json()
    assert len(configs) == 3
    keys = {c["config_key"] for c in configs}
    assert "search_weights" in keys
    assert "search_options" in keys
    assert "embedding_config" in keys


@pytest.mark.asyncio
async def test_get_config(client: AsyncClient, vet_user: User, db_session):
    await init_defaults(db_session)
    await db_session.commit()

    token = await _get_token(client, "13800000002", "vet123456")
    response = await client.get(
        "/api/v1/search-config/search_weights",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["config_key"] == "search_weights"
    assert "primary_diagnosis" in data["config_value"]


@pytest.mark.asyncio
async def test_get_config_not_found(client: AsyncClient, vet_user: User):
    token = await _get_token(client, "13800000002", "vet123456")
    response = await client.get(
        "/api/v1/search-config/nonexistent",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_config_requires_master(client: AsyncClient, vet_user: User, db_session):
    await init_defaults(db_session)
    await db_session.commit()

    token = await _get_token(client, "13800000002", "vet123456")
    response = await client.put(
        "/api/v1/search-config/search_weights",
        json={"config_value": {"primary_diagnosis": 5.0}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_config_by_master(
    client: AsyncClient, master_user: User, db_session
):
    await init_defaults(db_session)
    await db_session.commit()

    token = await _get_token(client, "13800000001", "master123")
    response = await client.put(
        "/api/v1/search-config/search_weights",
        json={
            "config_value": {"primary_diagnosis": 5.0, "symptoms": 3.0},
            "description": "更新后的权重",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["config_value"]["primary_diagnosis"] == 5.0
    assert data["description"] == "更新后的权重"
    assert data["updated_by"] == str(master_user.id)
