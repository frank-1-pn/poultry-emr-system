"""OpenAI 兼容适配器 — 同时作为 Kimi / DeepSeek 的基类"""

from typing import AsyncIterator

from openai import AsyncOpenAI

from app.adapters.base import BaseLLMAdapter, ChatMessage, ChatResponse

# 定价（元/千token）：input, output
OPENAI_PRICING = {
    "gpt-4o": (0.0175, 0.07),
    "gpt-4o-mini": (0.00105, 0.0042),
    "gpt-4-turbo": (0.07, 0.21),
    "gpt-3.5-turbo": (0.0035, 0.0105),
}

KIMI_PRICING = {
    "moonshot-v1-8k": (0.012, 0.012),
    "moonshot-v1-32k": (0.024, 0.024),
    "moonshot-v1-128k": (0.06, 0.06),
}

DEEPSEEK_PRICING = {
    "deepseek-chat": (0.001, 0.002),
    "deepseek-coder": (0.001, 0.002),
}


class OpenAICompatibleAdapter(BaseLLMAdapter):
    """OpenAI 兼容 API 适配器"""

    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    PRICING: dict[str, tuple[float, float]] = OPENAI_PRICING

    def __init__(self, api_key: str, model_name: str, api_endpoint: str | None = None, config: dict | None = None):
        super().__init__(api_key, model_name, api_endpoint, config)
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=api_endpoint or self.DEFAULT_BASE_URL,
            timeout=self.timeout,
        )

    async def chat_completion(self, messages: list[ChatMessage]) -> ChatResponse:
        start = self._measure_start()
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
        )
        latency = self._measure_latency(start)

        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else 0

        return ChatResponse(
            content=response.choices[0].message.content or "",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost=self.calculate_cost(input_tokens, output_tokens),
            latency_ms=latency,
        )

    async def chat_completion_stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = self.PRICING.get(self.model_name, (0.01, 0.03))
        return round(
            input_tokens / 1000 * pricing[0] + output_tokens / 1000 * pricing[1], 4
        )


class KimiAdapter(OpenAICompatibleAdapter):
    """Kimi（月之暗面）适配器 — OpenAI 兼容"""

    DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"
    PRICING = KIMI_PRICING


class DeepSeekAdapter(OpenAICompatibleAdapter):
    """DeepSeek 适配器 — OpenAI 兼容"""

    DEFAULT_BASE_URL = "https://api.deepseek.com"
    PRICING = DEEPSEEK_PRICING
