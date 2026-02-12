"""MiniMax 适配器（httpx 调用）"""

from typing import AsyncIterator

import httpx

from app.adapters.base import BaseLLMAdapter, ChatMessage, ChatResponse

MINIMAX_PRICING = {
    "abab6.5-chat": (0.03, 0.03),
    "abab6.5s-chat": (0.01, 0.01),
    "abab5.5-chat": (0.015, 0.015),
}

DEFAULT_ENDPOINT = "https://api.minimax.chat/v1/text/chatcompletion_v2"


class MiniMaxAdapter(BaseLLMAdapter):
    """MiniMax 适配器"""

    def __init__(self, api_key: str, model_name: str, api_endpoint: str | None = None, config: dict | None = None):
        super().__init__(api_key, model_name, api_endpoint, config)
        self.endpoint = api_endpoint or DEFAULT_ENDPOINT

    async def chat_completion(self, messages: list[ChatMessage]) -> ChatResponse:
        start = self._measure_start()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(self.endpoint, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        latency = self._measure_latency(start)

        if data.get("base_resp", {}).get("status_code", 0) != 0:
            raise RuntimeError(f"MiniMax API error: {data.get('base_resp', {}).get('status_msg')}")

        choice = data["choices"][0]
        content = choice["message"]["content"]
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        return ChatResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost=self.calculate_cost(input_tokens, output_tokens),
            latency_ms=latency,
        )

    async def chat_completion_stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "stream": True,
        }

        import json
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", self.endpoint, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        chunk_data = line[6:]
                        if chunk_data == "[DONE]":
                            break
                        chunk = json.loads(chunk_data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        if delta.get("content"):
                            yield delta["content"]

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = MINIMAX_PRICING.get(self.model_name, (0.01, 0.01))
        return round(
            input_tokens / 1000 * pricing[0] + output_tokens / 1000 * pricing[1], 4
        )
