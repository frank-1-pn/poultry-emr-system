"""DashScope (通义千问) Embedding 适配器"""

import asyncio

import dashscope
from dashscope import TextEmbedding

from app.adapters.embedding_base import BaseEmbeddingAdapter, EmbeddingResponse

# DashScope embedding 定价（元/千token）
DASHSCOPE_EMBEDDING_PRICING = {
    "text-embedding-v1": 0.0007,
    "text-embedding-v2": 0.0007,
    "text-embedding-v3": 0.0007,
}

# DashScope 单次最大 batch 数
DASHSCOPE_MAX_BATCH = 25


class DashScopeEmbeddingAdapter(BaseEmbeddingAdapter):
    """通义千问 DashScope Embedding 适配器"""

    def __init__(
        self,
        api_key: str,
        model_name: str = "text-embedding-v1",
        api_endpoint: str | None = None,
        dimensions: int = 1536,
    ):
        super().__init__(api_key, model_name, api_endpoint, dimensions)
        dashscope.api_key = api_key

    async def embed_texts(self, texts: list[str]) -> EmbeddingResponse:
        start = self._measure_start()
        all_embeddings: list[list[float]] = []
        total_tokens = 0

        # DashScope 限制每批 25 条
        for i in range(0, len(texts), DASHSCOPE_MAX_BATCH):
            batch = texts[i : i + DASHSCOPE_MAX_BATCH]
            response = await asyncio.to_thread(
                TextEmbedding.call,
                model=self.model_name,
                input=batch,
                text_type="document",
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"DashScope Embedding error: {response.code} - {response.message}"
                )

            for item in response.output["embeddings"]:
                all_embeddings.append(item["embedding"])
            total_tokens += response.usage.get("total_tokens", 0)

        latency = self._measure_latency(start)
        pricing = DASHSCOPE_EMBEDDING_PRICING.get(self.model_name, 0.0007)
        cost = round(total_tokens / 1000 * pricing, 6)

        return EmbeddingResponse(
            embeddings=all_embeddings,
            total_tokens=total_tokens,
            cost=cost,
            latency_ms=latency,
        )
