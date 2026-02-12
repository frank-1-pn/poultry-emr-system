"""OpenAI Embedding 适配器"""

from openai import AsyncOpenAI

from app.adapters.embedding_base import BaseEmbeddingAdapter, EmbeddingResponse

OPENAI_EMBEDDING_PRICING = {
    "text-embedding-ada-002": 0.0001,
    "text-embedding-3-small": 0.00002,
    "text-embedding-3-large": 0.00013,
}


class OpenAIEmbeddingAdapter(BaseEmbeddingAdapter):
    """OpenAI Embedding 适配器"""

    def __init__(
        self,
        api_key: str,
        model_name: str = "text-embedding-ada-002",
        api_endpoint: str | None = None,
        dimensions: int = 1536,
    ):
        super().__init__(api_key, model_name, api_endpoint, dimensions)
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=api_endpoint or "https://api.openai.com/v1",
            timeout=60,
        )

    async def embed_texts(self, texts: list[str]) -> EmbeddingResponse:
        start = self._measure_start()

        response = await self.client.embeddings.create(
            model=self.model_name,
            input=texts,
        )
        latency = self._measure_latency(start)

        embeddings = [item.embedding for item in response.data]
        total_tokens = response.usage.total_tokens if response.usage else 0
        pricing = OPENAI_EMBEDDING_PRICING.get(self.model_name, 0.0001)
        cost = round(total_tokens / 1000 * pricing, 6)

        return EmbeddingResponse(
            embeddings=embeddings,
            total_tokens=total_tokens,
            cost=cost,
            latency_ms=latency,
        )
