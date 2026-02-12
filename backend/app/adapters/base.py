"""LLM 适配器抽象基类"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class ChatResponse:
    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    latency_ms: int = 0


class BaseLLMAdapter(ABC):
    """LLM 适配器抽象基类，所有厂商适配器必须实现此接口"""

    def __init__(
        self,
        api_key: str,
        model_name: str,
        api_endpoint: str | None = None,
        config: dict | None = None,
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.api_endpoint = api_endpoint
        self.config = config or {}
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 2048)
        self.top_p = self.config.get("top_p", 1.0)
        self.timeout = self.config.get("timeout", 60)

    @abstractmethod
    async def chat_completion(self, messages: list[ChatMessage]) -> ChatResponse:
        """同步调用，返回完整响应"""
        ...

    @abstractmethod
    async def chat_completion_stream(
        self, messages: list[ChatMessage]
    ) -> AsyncIterator[str]:
        """流式调用，逐 token 返回"""
        ...

    @abstractmethod
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """计算成本（元）"""
        ...

    def _measure_start(self) -> float:
        return time.monotonic()

    def _measure_latency(self, start: float) -> int:
        return int((time.monotonic() - start) * 1000)
