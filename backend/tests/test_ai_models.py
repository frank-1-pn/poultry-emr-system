"""AI 模型管理模块测试"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.models.user import User
from app.utils.encryption import decrypt_api_key, encrypt_api_key


# ==================== 加密工具测试 ====================


@pytest.mark.asyncio
async def test_encrypt_decrypt_roundtrip():
    """加密/解密往返测试"""
    plaintext = "sk-test-key-1234567890"
    encrypted = encrypt_api_key(plaintext)
    assert encrypted != plaintext
    decrypted = decrypt_api_key(encrypted)
    assert decrypted == plaintext


@pytest.mark.asyncio
async def test_encrypt_different_ciphertext():
    """相同明文每次加密结果不同（Fernet 含时间戳）"""
    plaintext = "sk-test-key"
    enc1 = encrypt_api_key(plaintext)
    enc2 = encrypt_api_key(plaintext)
    assert enc1 != enc2
    assert decrypt_api_key(enc1) == plaintext
    assert decrypt_api_key(enc2) == plaintext


# ==================== Helper ====================


async def _get_master_token(client: AsyncClient, master_user: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"phone": "13800000001", "password": "master123"},
    )
    return resp.json()["access_token"]


async def _get_vet_token(client: AsyncClient, vet_user: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"phone": "13800000002", "password": "vet123456"},
    )
    return resp.json()["access_token"]


# ==================== API 测试 ====================


@pytest.mark.asyncio
async def test_create_model(client: AsyncClient, master_user: User):
    """Master 创建 AI 模型"""
    token = await _get_master_token(client, master_user)
    response = await client.post(
        "/api/v1/ai-models",
        json={
            "provider": "openai",
            "model_name": "gpt-4o",
            "display_name": "GPT-4o",
            "api_key": "sk-test-key-123",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "openai"
    assert data["model_name"] == "gpt-4o"
    assert data["display_name"] == "GPT-4o"
    assert data["api_key_set"] is True
    assert "api_key" not in data
    assert "api_key_encrypted" not in data


@pytest.mark.asyncio
async def test_list_models(client: AsyncClient, master_user: User):
    """列出 AI 模型"""
    token = await _get_master_token(client, master_user)
    # 创建一个模型
    await client.post(
        "/api/v1/ai-models",
        json={
            "provider": "qwen",
            "model_name": "qwen-max",
            "display_name": "通义千问 Max",
            "api_key": "sk-test",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    response = await client.get(
        "/api/v1/ai-models",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_update_model(client: AsyncClient, master_user: User):
    """更新模型配置"""
    token = await _get_master_token(client, master_user)
    create_resp = await client.post(
        "/api/v1/ai-models",
        json={
            "provider": "openai",
            "model_name": "gpt-4o-mini",
            "display_name": "GPT-4o Mini",
            "api_key": "sk-old-key",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    model_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/ai-models/{model_id}",
        json={"display_name": "GPT-4o Mini 更新"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["display_name"] == "GPT-4o Mini 更新"


@pytest.mark.asyncio
async def test_set_default_model(client: AsyncClient, master_user: User):
    """设置默认模型"""
    token = await _get_master_token(client, master_user)

    # 创建两个模型
    resp1 = await client.post(
        "/api/v1/ai-models",
        json={
            "provider": "openai",
            "model_name": "gpt-4o",
            "display_name": "Model A",
            "api_key": "sk-a",
            "is_default": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    id_a = resp1.json()["id"]
    assert resp1.json()["is_default"] is True

    resp2 = await client.post(
        "/api/v1/ai-models",
        json={
            "provider": "qwen",
            "model_name": "qwen-max",
            "display_name": "Model B",
            "api_key": "sk-b",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    id_b = resp2.json()["id"]

    # 设置 B 为默认
    resp = await client.post(
        f"/api/v1/ai-models/{id_b}/set-default",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_default"] is True

    # 确认 A 不再是默认
    resp_a = await client.get(
        f"/api/v1/ai-models/{id_a}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_a.json()["is_default"] is False


@pytest.mark.asyncio
async def test_delete_model(client: AsyncClient, master_user: User):
    """停用模型"""
    token = await _get_master_token(client, master_user)
    create_resp = await client.post(
        "/api/v1/ai-models",
        json={
            "provider": "deepseek",
            "model_name": "deepseek-chat",
            "display_name": "DeepSeek",
            "api_key": "sk-ds",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    model_id = create_resp.json()["id"]

    response = await client.delete(
        f"/api/v1/ai-models/{model_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_non_master_forbidden(client: AsyncClient, vet_user: User):
    """非 Master 用户调用管理 API → 403"""
    token = await _get_vet_token(client, vet_user)
    response = await client.get(
        "/api/v1/ai-models",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_non_master_create_forbidden(client: AsyncClient, vet_user: User):
    """非 Master 用户创建模型 → 403"""
    token = await _get_vet_token(client, vet_user)
    response = await client.post(
        "/api/v1/ai-models",
        json={
            "provider": "openai",
            "model_name": "gpt-4o",
            "display_name": "GPT",
            "api_key": "sk-test",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


# ==================== 适配器工厂测试 ====================


@pytest.mark.asyncio
async def test_adapter_factory_create():
    """适配器工厂创建测试（仅测试已安装 SDK 的适配器）"""
    from app.adapters.base import BaseLLMAdapter
    from app.adapters.factory import LLMAdapterFactory

    # OpenAI 系列（openai 已安装）
    adapter = LLMAdapterFactory.create_adapter("openai", "sk-test", "gpt-4o")
    assert isinstance(adapter, BaseLLMAdapter)

    adapter = LLMAdapterFactory.create_adapter("kimi", "sk-test", "moonshot-v1-8k")
    assert isinstance(adapter, BaseLLMAdapter)

    adapter = LLMAdapterFactory.create_adapter("deepseek", "sk-test", "deepseek-chat")
    assert isinstance(adapter, BaseLLMAdapter)


@pytest.mark.asyncio
async def test_adapter_factory_invalid_provider():
    """不支持的提供商"""
    from app.adapters.factory import LLMAdapterFactory

    with pytest.raises(ValueError, match="不支持的模型提供商"):
        LLMAdapterFactory.create_adapter("unknown", "key", "model")


@pytest.mark.asyncio
async def test_usage_stats_empty(client: AsyncClient, master_user: User):
    """空的使用统计"""
    token = await _get_master_token(client, master_user)
    response = await client.get(
        "/api/v1/ai-models/usage-stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == []
