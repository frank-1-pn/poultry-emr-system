"""Google Gemini 适配器"""

import asyncio
from typing import AsyncIterator

import google.generativeai as genai

from app.adapters.base import BaseLLMAdapter, ChatMessage, ChatResponse

GEMINI_PRICING = {
    "gemini-pro": (0.0035, 0.0105),
    "gemini-1.5-pro": (0.0245, 0.0735),
    "gemini-1.5-flash": (0.00525, 0.021),
    "gemini-2.0-flash": (0.007, 0.021),
}


class GeminiAdapter(BaseLLMAdapter):
    """Google Gemini 适配器"""

    def __init__(self, api_key: str, model_name: str, api_endpoint: str | None = None, config: dict | None = None):
        super().__init__(api_key, model_name, api_endpoint, config)
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    async def chat_completion(self, messages: list[ChatMessage]) -> ChatResponse:
        start = self._measure_start()

        # 将消息转换为 Gemini 格式
        history = []
        last_content = ""
        for m in messages:
            if m.role == "system":
                # Gemini 没有 system role，作为 user 上下文
                history.append({"role": "user", "parts": [m.content]})
                history.append({"role": "model", "parts": ["好的，我了解了。"]})
            elif m.role == "user":
                last_content = m.content
            elif m.role == "assistant":
                history.append({"role": "model", "parts": [m.content]})

        chat = self.model.start_chat(history=history)
        response = await asyncio.to_thread(
            chat.send_message,
            last_content,
            generation_config=genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
                top_p=self.top_p,
            ),
        )
        latency = self._measure_latency(start)

        content = response.text
        # Gemini 的 token 计数
        input_tokens = response.usage_metadata.prompt_token_count if hasattr(response, "usage_metadata") and response.usage_metadata else 0
        output_tokens = response.usage_metadata.candidates_token_count if hasattr(response, "usage_metadata") and response.usage_metadata else 0

        return ChatResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost=self.calculate_cost(input_tokens, output_tokens),
            latency_ms=latency,
        )

    async def chat_completion_stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        history = []
        last_content = ""
        for m in messages:
            if m.role == "system":
                history.append({"role": "user", "parts": [m.content]})
                history.append({"role": "model", "parts": ["好的，我了解了。"]})
            elif m.role == "user":
                last_content = m.content
            elif m.role == "assistant":
                history.append({"role": "model", "parts": [m.content]})

        chat = self.model.start_chat(history=history)
        response = await asyncio.to_thread(
            chat.send_message,
            last_content,
            generation_config=genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
                top_p=self.top_p,
            ),
            stream=True,
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = GEMINI_PRICING.get(self.model_name, (0.0035, 0.0105))
        return round(
            input_tokens / 1000 * pricing[0] + output_tokens / 1000 * pricing[1], 4
        )
