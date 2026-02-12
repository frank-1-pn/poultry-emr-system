"""Soul 模块测试"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.soul import MemoryEntry, SoulConfig
from app.models.user import User
from app.utils.token_utils import compress_markdown, count_tokens, select_memories


# ── Token 工具测试 ──

class TestTokenUtils:
    def test_count_tokens_empty(self):
        assert count_tokens("") == 0

    def test_count_tokens_basic(self):
        tokens = count_tokens("Hello, world!")
        assert tokens > 0

    def test_compress_markdown_within_budget(self):
        """原文在预算内，不压缩"""
        content = "# Title\n\nShort content."
        result = compress_markdown(content, 1000)
        assert result == content

    def test_compress_markdown_large_text(self):
        """大文本压缩到预算内"""
        content = "# 禽类 EMR 助手\n\n"
        content += "## 身份与角色\n\n" + "这是一段很长的描述。\n" * 50
        content += "\n## 沟通风格\n\n" + "- 使用专业但易懂的中文\n" * 30
        content += "\n## 核心技能\n\n" + "- 禽类常见病诊断辅助\n" * 30
        content += "\n## 注意事项\n\n" + "- 永远提醒用户确认休药期\n" * 30

        budget = 200
        result = compress_markdown(content, budget)
        result_tokens = count_tokens(result)
        assert result_tokens <= budget

    def test_compress_preserves_headers(self):
        """压缩后保留标题"""
        content = "## 身份\n\n详细内容。\n\n## 技能\n\n更多内容。"
        result = compress_markdown(content, 1000)
        assert "## 身份" in result
        assert "## 技能" in result

    def test_select_memories_empty(self):
        text, count = select_memories([], 500)
        assert text == ""
        assert count == 0

    def test_select_memories_budget_limit(self):
        """条目超过预算时截断"""

        class FakeEntry:
            def __init__(self, cat, content):
                self.category = cat
                self.content = content

        entries = [
            FakeEntry("skill", f"记忆条目内容 {i} " + "额外文本" * 20)
            for i in range(20)
        ]
        text, loaded = select_memories(entries, 100)
        assert loaded < 20
        assert count_tokens(text) <= 100


# ── API 测试 ──

def _auth_header(user: User) -> dict:
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
class TestSoulAPI:
    async def test_create_soul(self, client: AsyncClient, master_user: User):
        """管理员创建 Soul"""
        resp = await client.post(
            "/api/v1/soul",
            json={"title": "v1-初始版本", "content": "# 禽类 EMR 助手\n\n## 身份\n\n你是助手。"},
            headers=_auth_header(master_user),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "v1-初始版本"
        assert data["is_active"] is True
        assert data["token_count"] > 0
        assert data["content_compressed"]

    async def test_create_soul_forbidden_for_vet(self, client: AsyncClient, vet_user: User):
        """非管理员不能创建 Soul"""
        resp = await client.post(
            "/api/v1/soul",
            json={"title": "test", "content": "test"},
            headers=_auth_header(vet_user),
        )
        assert resp.status_code == 403

    async def test_get_active_soul(self, client: AsyncClient, master_user: User):
        """获取当前生效 Soul"""
        # 先创建
        await client.post(
            "/api/v1/soul",
            json={"title": "v1", "content": "# Test Soul"},
            headers=_auth_header(master_user),
        )
        resp = await client.get(
            "/api/v1/soul/active",
            headers=_auth_header(master_user),
        )
        assert resp.status_code == 200

    async def test_soul_versions(self, client: AsyncClient, master_user: User):
        """版本列表"""
        headers = _auth_header(master_user)
        await client.post("/api/v1/soul", json={"title": "v1", "content": "# V1"}, headers=headers)
        await client.post("/api/v1/soul", json={"title": "v2", "content": "# V2"}, headers=headers)

        resp = await client.get("/api/v1/soul/versions", headers=headers)
        assert resp.status_code == 200
        versions = resp.json()
        assert len(versions) >= 2

    async def test_activate_soul(self, client: AsyncClient, master_user: User):
        """切换生效版本"""
        headers = _auth_header(master_user)
        r1 = await client.post("/api/v1/soul", json={"title": "v1", "content": "# V1"}, headers=headers)
        r2 = await client.post("/api/v1/soul", json={"title": "v2", "content": "# V2"}, headers=headers)
        soul_id_1 = r1.json()["id"]

        resp = await client.post(f"/api/v1/soul/{soul_id_1}/activate", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True

    async def test_preview_soul(self, client: AsyncClient, master_user: User):
        """预览压缩效果"""
        headers = _auth_header(master_user)
        r = await client.post(
            "/api/v1/soul",
            json={"title": "v1", "content": "# 助手\n\n## 身份\n\n详细描述。"},
            headers=headers,
        )
        soul_id = r.json()["id"]
        resp = await client.get(f"/api/v1/soul/{soul_id}/preview", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "original_tokens" in data
        assert "compressed_tokens" in data


@pytest.mark.asyncio
class TestMemoryAPI:
    async def test_add_memory(self, client: AsyncClient, master_user: User):
        """添加记忆条目"""
        resp = await client.post(
            "/api/v1/soul/memory",
            json={
                "category": "skill",
                "content": "擅长禽类呼吸道疾病诊断",
                "importance": 4,
                "source": "manual",
            },
            headers=_auth_header(master_user),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["category"] == "skill"
        assert data["importance"] == 4

    async def test_list_memories(self, client: AsyncClient, master_user: User):
        """列出记忆条目"""
        headers = _auth_header(master_user)
        await client.post(
            "/api/v1/soul/memory",
            json={"category": "style", "content": "友善沟通", "importance": 3, "source": "manual"},
            headers=headers,
        )
        resp = await client.get("/api/v1/soul/memory", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_list_memories_filter_category(self, client: AsyncClient, master_user: User):
        """按分类过滤"""
        headers = _auth_header(master_user)
        await client.post(
            "/api/v1/soul/memory",
            json={"category": "habit", "content": "习惯1", "importance": 2, "source": "manual"},
            headers=headers,
        )
        resp = await client.get("/api/v1/soul/memory?category=habit", headers=headers)
        assert resp.status_code == 200
        for item in resp.json():
            assert item["category"] == "habit"

    async def test_archive_memory(self, client: AsyncClient, master_user: User):
        """归档记忆条目"""
        headers = _auth_header(master_user)
        r = await client.post(
            "/api/v1/soul/memory",
            json={"category": "feedback", "content": "旧反馈", "importance": 1, "source": "manual"},
            headers=headers,
        )
        memory_id = r.json()["id"]
        resp = await client.delete(f"/api/v1/soul/memory/{memory_id}", headers=headers)
        assert resp.status_code == 200
        assert "已归档" in resp.json()["message"]

    async def test_update_memory(self, client: AsyncClient, master_user: User):
        """更新记忆条目"""
        headers = _auth_header(master_user)
        r = await client.post(
            "/api/v1/soul/memory",
            json={"category": "skill", "content": "原始内容", "importance": 2, "source": "manual"},
            headers=headers,
        )
        memory_id = r.json()["id"]
        resp = await client.patch(
            f"/api/v1/soul/memory/{memory_id}",
            json={"content": "更新后的内容", "importance": 5},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["content"] == "更新后的内容"
        assert resp.json()["importance"] == 5


@pytest.mark.asyncio
class TestContextAPI:
    async def test_get_context(self, client: AsyncClient, master_user: User):
        """获取拼装好的上下文"""
        headers = _auth_header(master_user)

        # 创建 Soul
        await client.post(
            "/api/v1/soul",
            json={"title": "v1", "content": "# 助手\n\n## 身份\n\n你是禽类诊疗助手。"},
            headers=headers,
        )
        # 添加 Memory
        await client.post(
            "/api/v1/soul/memory",
            json={"category": "skill", "content": "呼吸道疾病", "importance": 5, "source": "manual"},
            headers=headers,
        )

        resp = await client.get("/api/v1/soul/context", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "soul_content" in data
        assert "memory_content" in data
        assert "total_tokens" in data
        assert data["total_tokens"] > 0
        assert data["metadata"]["soul_version"] == "v1"
        assert data["metadata"]["memory_loaded"] >= 1

    async def test_context_accessible_by_vet(self, client: AsyncClient, master_user: User, vet_user: User):
        """普通兽医也能获取上下文"""
        # Master 先创建 Soul
        await client.post(
            "/api/v1/soul",
            json={"title": "v1", "content": "# Test"},
            headers=_auth_header(master_user),
        )
        # Vet 获取上下文
        resp = await client.get(
            "/api/v1/soul/context",
            headers=_auth_header(vet_user),
        )
        assert resp.status_code == 200
