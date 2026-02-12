"""Anthropic Claude 适配器"""

from typing import AsyncIterator

from anthropic import AsyncAnthropic

from app.adapters.base import BaseLLMAdapter, ChatMessage, ChatResponse

CLAUDE_PRICING = {
    "claude-sonnet-4-5-20250929": (0.021, 0.105),
    "claude-opus-4-6": (0.105, 0.525),
    "claude-haiku-4-5-20251001": (0.007, 0.035),
    "claude-3-5-sonnet-20241022": (0.021, 0.105),
    "claude-3-opus-20240229": (0.105, 0.525),
    "claude-3-haiku-20240307": (0.00175, 0.00875),
}


class ClaudeAdapter(BaseLLMAdapter):
    """Anthropic Claude 适配器"""

    def __init__(self, api_key: str, model_name: str, api_endpoint: str | None = None, config: dict | None = None):
        super().__init__(api_key, model_name, api_endpoint, config)
        kwargs = {"api_key": api_key, "timeout": self.timeout}
        if api_endpoint:
            kwargs["base_url"] = api_endpoint
        self.client = AsyncAnthropic(**kwargs)

    async def chat_completion(self, messages: list[ChatMessage]) -> ChatResponse:
        start = self._measure_start()

        # Claude 的 system 消息需要单独传
        system_msg = None
        chat_msgs = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                chat_msgs.append({"role": m.role, "content": m.content})

        kwargs = {
            "model": self.model_name,
            "messages": chat_msgs,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }
        if system_msg:
            kwargs["system"] = system_msg

        response = await self.client.messages.create(**kwargs)
        latency = self._measure_latency(start)

        content = response.content[0].text if response.content else ""
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        return ChatResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost=self.calculate_cost(input_tokens, output_tokens),
            latency_ms=latency,
        )

    async def chat_completion_stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        system_msg = None
        chat_msgs = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                chat_msgs.append({"role": m.role, "content": m.content})

        kwargs = {
            "model": self.model_name,
            "messages": chat_msgs,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "stream": True,
        }
        if system_msg:
            kwargs["system"] = system_msg

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = CLAUDE_PRICING.get(self.model_name, (0.021, 0.105))
        return round(
            input_tokens / 1000 * pricing[0] + output_tokens / 1000 * pricing[1], 4
        )
