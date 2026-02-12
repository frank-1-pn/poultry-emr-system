"""AI 对话式病历录入测试"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base import ChatResponse
from app.core.security import create_access_token
from app.models.ai_model import AIModel
from app.models.user import User
from app.utils.encryption import encrypt_api_key


def _make_token(user: User) -> str:
    return create_access_token({"sub": str(user.id)})


def _mock_llm_response(
    reply: str = "好的，请告诉我更多信息。",
    extracted_info: dict | None = None,
    completeness: dict | None = None,
) -> ChatResponse:
    """构造模拟的 LLM 返回"""
    content = json.dumps(
        {
            "reply": reply,
            "extracted_info": extracted_info or {},
            "confidence_scores": {k: 0.9 for k in (extracted_info or {})},
            "needs_confirmation": [],
            "completeness": completeness or {},
            "suggested_state": "collecting_basic",
        },
        ensure_ascii=False,
    )
    return ChatResponse(
        content=content,
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        cost=0.001,
        latency_ms=500,
    )


@pytest_asyncio.fixture
async def ai_model(db_session: AsyncSession, master_user: User) -> AIModel:
    """创建测试用 AI 模型"""
    model = AIModel(
        provider="openai",
        model_name="gpt-4",
        display_name="Test GPT-4",
        api_key_encrypted=encrypt_api_key("test-key"),
        is_active=True,
        is_default=True,
        created_by=master_user.id,
    )
    db_session.add(model)
    await db_session.commit()
    await db_session.refresh(model)
    return model


@pytest.mark.asyncio
async def test_create_conversation(client: AsyncClient, vet_user: User):
    """测试创建对话"""
    token = _make_token(vet_user)
    response = await client.post(
        "/api/v1/conversations",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["state"] == "collecting_basic"
    assert data["user_id"] == str(vet_user.id)


@pytest.mark.asyncio
async def test_list_conversations(client: AsyncClient, vet_user: User):
    """测试获取对话列表"""
    token = _make_token(vet_user)

    # 创建两个对话
    await client.post(
        "/api/v1/conversations",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        "/api/v1/conversations",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = await client.get(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_conversation(client: AsyncClient, vet_user: User):
    """测试获取对话详情"""
    token = _make_token(vet_user)

    create_resp = await client.post(
        "/api/v1/conversations",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    conv_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == conv_id


@pytest.mark.asyncio
async def test_get_messages(client: AsyncClient, vet_user: User):
    """测试获取消息历史（含初始引导消息）"""
    token = _make_token(vet_user)

    create_resp = await client.post(
        "/api/v1/conversations",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    conv_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1  # 初始引导消息
    assert data["items"][0]["role"] == "assistant"


@pytest.mark.asyncio
async def test_send_message(
    client: AsyncClient, vet_user: User, ai_model: AIModel
):
    """测试发送消息并获取 AI 回复"""
    token = _make_token(vet_user)

    # 创建对话
    create_resp = await client.post(
        "/api/v1/conversations",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    conv_id = create_resp.json()["id"]

    # Mock LLM adapter
    mock_adapter = AsyncMock()
    mock_adapter.chat_completion = AsyncMock(
        return_value=_mock_llm_response(
            reply="了解，您养的是蛋鸡，请问出现了什么症状？",
            extracted_info={"poultry_type": "蛋鸡"},
            completeness={"poultry_type": True, "symptoms": False},
        )
    )

    with patch(
        "app.services.conversation_service._get_adapter_and_model",
        return_value=(mock_adapter, ai_model),
    ):
        response = await client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            json={"content": "我养的是蛋鸡，最近有些不太对劲"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "蛋鸡" in data["message"]["content"]
    assert data["collected_info"].get("poultry_type") == "蛋鸡"


@pytest.mark.asyncio
async def test_complete_conversation(
    client: AsyncClient, vet_user: User, ai_model: AIModel
):
    """测试完成对话并保存病历"""
    token = _make_token(vet_user)

    # 创建对话
    create_resp = await client.post(
        "/api/v1/conversations",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    conv_id = create_resp.json()["id"]

    # Mock LLM 并发送消息收集信息
    mock_adapter = AsyncMock()
    mock_adapter.chat_completion = AsyncMock(
        return_value=_mock_llm_response(
            reply="信息已收集完毕，是否确认保存？",
            extracted_info={
                "poultry_type": "蛋鸡",
                "visit_date": "2026-02-11",
                "symptoms": ["精神萎靡", "采食量下降", "产蛋率降低"],
                "primary_diagnosis": "新城疫疑似",
                "severity": "moderate",
            },
            completeness={
                "poultry_type": True,
                "visit_date": True,
                "symptoms": True,
                "primary_diagnosis": True,
                "severity": True,
            },
        )
    )

    with patch(
        "app.services.conversation_service._get_adapter_and_model",
        return_value=(mock_adapter, ai_model),
    ):
        await client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            json={"content": "蛋鸡，精神萎靡，采食量下降，产蛋率降低，疑似新城疫"},
            headers={"Authorization": f"Bearer {token}"},
        )

    # 确认保存
    response = await client.post(
        f"/api/v1/conversations/{conv_id}/complete",
        json={"confirmed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["record_no"].startswith("EMR-")
    assert data["conversation"]["status"] == "completed"


@pytest.mark.asyncio
async def test_pause_resume_conversation(client: AsyncClient, vet_user: User):
    """测试暂停和恢复对话"""
    token = _make_token(vet_user)

    create_resp = await client.post(
        "/api/v1/conversations",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    conv_id = create_resp.json()["id"]

    # 暂停
    pause_resp = await client.post(
        f"/api/v1/conversations/{conv_id}/pause",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert pause_resp.status_code == 200
    assert pause_resp.json()["status"] == "paused"

    # 恢复
    resume_resp = await client.post(
        f"/api/v1/conversations/{conv_id}/resume",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resume_resp.status_code == 200
    assert resume_resp.json()["status"] == "active"


@pytest.mark.asyncio
async def test_conversation_access_control(
    client: AsyncClient, vet_user: User, master_user: User
):
    """测试对话归属验证"""
    vet_token = _make_token(vet_user)
    master_token = _make_token(master_user)

    # vet 用户创建对话
    create_resp = await client.post(
        "/api/v1/conversations",
        json={},
        headers={"Authorization": f"Bearer {vet_token}"},
    )
    conv_id = create_resp.json()["id"]

    # master 用户尝试访问（应该 403）
    response = await client.get(
        f"/api/v1/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {master_token}"},
    )
    assert response.status_code == 403
