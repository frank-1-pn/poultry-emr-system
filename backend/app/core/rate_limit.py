"""API 限流中间件 — 基于内存的滑动窗口限流器"""

import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """简单的内存滑动窗口限流器。生产环境可替换为 Redis 实现。"""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _cleanup(self, key: str, now: float) -> None:
        cutoff = now - self.window_seconds
        self._requests[key] = [
            t for t in self._requests[key] if t > cutoff
        ]

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        self._cleanup(key, now)
        if len(self._requests[key]) >= self.max_requests:
            return False
        self._requests[key].append(now)
        return True

    def remaining(self, key: str) -> int:
        now = time.time()
        self._cleanup(key, now)
        return max(0, self.max_requests - len(self._requests[key]))


# 全局限流器实例
global_limiter = RateLimiter(max_requests=60, window_seconds=60)
# 认证端点更严格
auth_limiter = RateLimiter(max_requests=10, window_seconds=60)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 跳过健康检查和文档
        path = request.url.path
        if path in ("/health", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        # 测试环境跳过限流
        from app.core.config import get_settings
        if get_settings().DEBUG:
            return await call_next(request)

        # 获取客户端标识
        client_ip = request.client.host if request.client else "unknown"

        # 认证端点使用更严格的限流
        if "/auth/" in path:
            limiter = auth_limiter
        else:
            limiter = global_limiter

        if not limiter.is_allowed(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求过于频繁，请稍后再试",
                headers={"Retry-After": str(limiter.window_seconds)},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(
            limiter.remaining(client_ip)
        )
        return response
