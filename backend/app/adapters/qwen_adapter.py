"""通义千问（DashScope）适配器"""

from typing import AsyncIterator

import dashscope
from dashscope import Generation

from app.adapters.base import BaseLLMAdapter, ChatMessage, ChatResponse

QWEN_PRICING = {
    "qwen-max": (0.04, 0.12),
    "qwen-plus": (0.004, 0.012),
    "qwen-turbo": (0.002, 0.006),
    "qwen-long": (0.0005, 0.002),
}


class QwenAdapter(BaseLLMAdapter):
    """通义千问适配器（DashScope SDK）"""

    def __init__(self, api_key: str, model_name: str, api_endpoint: str | None = None, config: dict | None = None):
        super().__init__(api_key, model_name, api_endpoint, config)
        dashscope.api_key = api_key

    async def chat_completion(self, messages: list[ChatMessage]) -> ChatResponse:
        start = self._measure_start()

        # DashScope 同步调用，在线程池中运行
        import asyncio
        response = await asyncio.to_thread(
            Generation.call,
            model=self.model_name,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            result_format="message",
        )
        latency = self._measure_latency(start)

        if response.status_code != 200:
            raise RuntimeError(f"Qwen API error: {response.code} - {response.message}")

        content = response.output.choices[0].message.content
        usage = response.usage
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        return ChatResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost=self.calculate_cost(input_tokens, output_tokens),
            latency_ms=latency,
        )

    async def chat_completion_stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        import asyncio

        def _stream():
            responses = Generation.call(
                model=self.model_name,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                result_format="message",
                stream=True,
                incremental_output=True,
            )
            for response in responses:
                if response.status_code == 200:
                    yield response.output.choices[0].message.content

        loop = asyncio.get_event_loop()
        # 将同步生成器包装为异步
        chunks = await asyncio.to_thread(lambda: list(_stream()))
        for chunk in chunks:
            yield chunk

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = QWEN_PRICING.get(self.model_name, (0.004, 0.012))
        return round(
            input_tokens / 1000 * pricing[0] + output_tokens / 1000 * pricing[1], 4
        )
