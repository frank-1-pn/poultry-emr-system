"""Embedding 适配器抽象基类"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class EmbeddingResponse:
    embeddings: list[list[float]]
    total_tokens: int = 0
    cost: float = 0.0
    latency_ms: int = 0


class BaseEmbeddingAdapter(ABC):
    """Embedding 适配器抽象基类，所有 Embedding 厂商适配器必须实现此接口"""

    def __init__(
        self,
        api_key: str,
        model_name: str,
        api_endpoint: str | None = None,
        dimensions: int = 1536,
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.api_endpoint = api_endpoint
        self.dimensions = dimensions

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> EmbeddingResponse:
        """批量生成文本 embedding"""
        ...

    async def embed_text(self, text: str) -> list[float]:
        """单条文本 embedding（便捷方法）"""
        response = await self.embed_texts([text])
        return response.embeddings[0]

    def _measure_start(self) -> float:
        return time.monotonic()

    def _measure_latency(self, start: float) -> int:
        return int((time.monotonic() - start) * 1000)
