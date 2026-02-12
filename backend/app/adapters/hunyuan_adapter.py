"""腾讯混元适配器"""

import asyncio
import json
from typing import AsyncIterator

from app.adapters.base import BaseLLMAdapter, ChatMessage, ChatResponse

HUNYUAN_PRICING = {
    "hunyuan-lite": (0.008, 0.008),
    "hunyuan-standard": (0.045, 0.045),
    "hunyuan-pro": (0.1, 0.1),
}


class HunyuanAdapter(BaseLLMAdapter):
    """腾讯混元适配器（使用腾讯云 SDK）"""

    def __init__(self, api_key: str, model_name: str, api_endpoint: str | None = None, config: dict | None = None):
        super().__init__(api_key, model_name, api_endpoint, config)
        # api_key 格式: "secret_id:secret_key"
        parts = api_key.split(":", 1)
        if len(parts) != 2:
            raise ValueError("混元 API Key 格式应为 'secret_id:secret_key'")
        self.secret_id = parts[0]
        self.secret_key = parts[1]

    def _get_client(self):
        from tencentcloud.common import credential
        from tencentcloud.hunyuan.v20230901 import hunyuan_client, models

        cred = credential.Credential(self.secret_id, self.secret_key)
        client = hunyuan_client.HunyuanClient(cred, "")
        return client, models

    async def chat_completion(self, messages: list[ChatMessage]) -> ChatResponse:
        start = self._measure_start()

        def _call():
            client, models = self._get_client()
            req = models.ChatCompletionsRequest()
            req.Model = self.model_name
            req.Messages = [
                {"Role": m.role if m.role != "assistant" else "assistant", "Content": m.content}
                for m in messages
            ]
            req.Temperature = self.temperature
            req.TopP = self.top_p
            req.Stream = False
            return client.ChatCompletions(req)

        response = await asyncio.to_thread(_call)
        latency = self._measure_latency(start)

        content = response.Choices[0].Message.Content
        usage = response.Usage
        input_tokens = usage.PromptTokens if usage else 0
        output_tokens = usage.CompletionTokens if usage else 0

        return ChatResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost=self.calculate_cost(input_tokens, output_tokens),
            latency_ms=latency,
        )

    async def chat_completion_stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        def _stream():
            client, models = self._get_client()
            req = models.ChatCompletionsRequest()
            req.Model = self.model_name
            req.Messages = [
                {"Role": m.role, "Content": m.content}
                for m in messages
            ]
            req.Temperature = self.temperature
            req.TopP = self.top_p
            req.Stream = True
            resp = client.ChatCompletions(req)
            results = []
            for event in resp:
                data = json.loads(event["data"])
                if data.get("Choices"):
                    delta = data["Choices"][0].get("Delta", {})
                    if delta.get("Content"):
                        results.append(delta["Content"])
            return results

        chunks = await asyncio.to_thread(_stream)
        for chunk in chunks:
            yield chunk

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = HUNYUAN_PRICING.get(self.model_name, (0.045, 0.045))
        return round(
            input_tokens / 1000 * pricing[0] + output_tokens / 1000 * pricing[1], 4
        )
