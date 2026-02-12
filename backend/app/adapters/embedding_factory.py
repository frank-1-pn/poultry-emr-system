"""Embedding 适配器工厂 — 延迟导入以避免缺少 SDK 时导入失败"""

from app.adapters.embedding_base import BaseEmbeddingAdapter
from app.core.config import get_settings

# provider -> (module_path, class_name)
_EMBEDDING_REGISTRY: dict[str, tuple[str, str]] = {
    "dashscope": (
        "app.adapters.embedding_dashscope",
        "DashScopeEmbeddingAdapter",
    ),
    "openai": (
        "app.adapters.embedding_openai",
        "OpenAIEmbeddingAdapter",
    ),
}


def _load_embedding_class(provider: str) -> type[BaseEmbeddingAdapter]:
    entry = _EMBEDDING_REGISTRY.get(provider)
    if not entry:
        raise ValueError(f"不支持的 Embedding 提供商: {provider}")
    import importlib
    module_path, class_name = entry
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


class EmbeddingAdapterFactory:
    """Embedding 适配器工厂"""

    @staticmethod
    def create_adapter(
        provider: str,
        api_key: str,
        model_name: str,
        api_endpoint: str | None = None,
        dimensions: int = 1536,
    ) -> BaseEmbeddingAdapter:
        adapter_cls = _load_embedding_class(provider)
        return adapter_cls(
            api_key=api_key,
            model_name=model_name,
            api_endpoint=api_endpoint,
            dimensions=dimensions,
        )

    @staticmethod
    def get_default_adapter() -> BaseEmbeddingAdapter:
        """根据 Settings 配置创建默认 embedding 适配器。
        EMBEDDING_API_KEY 为空时，尝试从数据库获取对应提供商的 LLM key。
        """
        settings = get_settings()
        api_key = settings.EMBEDDING_API_KEY

        if not api_key:
            # 尝试从环境变量获取对应提供商的 key
            import os
            provider = settings.EMBEDDING_PROVIDER
            fallback_keys = {
                "dashscope": "QWEN_API_KEY",
                "openai": "OPENAI_API_KEY",
            }
            env_var = fallback_keys.get(provider)
            if env_var:
                api_key = os.environ.get(env_var, "")
            if not api_key:
                raise ValueError(
                    f"未配置 EMBEDDING_API_KEY，且无法从 {env_var or provider} 获取备用 key"
                )

        return EmbeddingAdapterFactory.create_adapter(
            provider=settings.EMBEDDING_PROVIDER,
            api_key=api_key,
            model_name=settings.EMBEDDING_MODEL,
            dimensions=settings.EMBEDDING_DIMENSIONS,
        )
