"""LLM 适配器工厂 — 延迟导入各适配器以避免缺少 SDK 时导入失败"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base import BaseLLMAdapter

# provider -> (module_path, class_name)
_ADAPTER_REGISTRY: dict[str, tuple[str, str]] = {
    "openai": ("app.adapters.openai_adapter", "OpenAICompatibleAdapter"),
    "kimi": ("app.adapters.openai_adapter", "KimiAdapter"),
    "deepseek": ("app.adapters.openai_adapter", "DeepSeekAdapter"),
    "claude": ("app.adapters.claude_adapter", "ClaudeAdapter"),
    "qwen": ("app.adapters.qwen_adapter", "QwenAdapter"),
    "minimax": ("app.adapters.minimax_adapter", "MiniMaxAdapter"),
    "gemini": ("app.adapters.gemini_adapter", "GeminiAdapter"),
    "hunyuan": ("app.adapters.hunyuan_adapter", "HunyuanAdapter"),
}


def _load_adapter_class(provider: str) -> type[BaseLLMAdapter]:
    """延迟加载适配器类"""
    entry = _ADAPTER_REGISTRY.get(provider)
    if not entry:
        raise ValueError(f"不支持的模型提供商: {provider}")
    module_path, class_name = entry
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


class LLMAdapterFactory:
    """LLM 适配器工厂"""

    @staticmethod
    def create_adapter(
        provider: str,
        api_key: str,
        model_name: str,
        api_endpoint: str | None = None,
        config: dict | None = None,
    ) -> BaseLLMAdapter:
        adapter_cls = _load_adapter_class(provider)
        return adapter_cls(
            api_key=api_key,
            model_name=model_name,
            api_endpoint=api_endpoint,
            config=config,
        )

    @staticmethod
    async def get_default_adapter(db: AsyncSession) -> BaseLLMAdapter:
        """从数据库获取默认模型并创建适配器"""
        from app.models.ai_model import AIModel
        from app.utils.encryption import decrypt_api_key

        result = await db.execute(
            select(AIModel).where(AIModel.is_default == True, AIModel.is_active == True)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError("未配置默认 AI 模型")

        api_key = decrypt_api_key(model.api_key_encrypted)
        return LLMAdapterFactory.create_adapter(
            provider=model.provider,
            api_key=api_key,
            model_name=model.model_name,
            api_endpoint=model.api_endpoint,
            config=model.config,
        )
