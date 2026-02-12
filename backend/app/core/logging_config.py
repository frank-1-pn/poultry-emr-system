"""结构化日志 + 脱敏配置"""

import logging
import re
import sys

# 敏感字段正则模式
SENSITIVE_PATTERNS = [
    (re.compile(r'("password"\s*:\s*)"[^"]*"'), r'\1"***"'),
    (re.compile(r'("password_hash"\s*:\s*)"[^"]*"'), r'\1"***"'),
    (re.compile(r'("access_token"\s*:\s*)"[^"]*"'), r'\1"***"'),
    (re.compile(r'("refresh_token"\s*:\s*)"[^"]*"'), r'\1"***"'),
    (re.compile(r'("security_token"\s*:\s*)"[^"]*"'), r'\1"***"'),
    (re.compile(r'("access_key_secret"\s*:\s*)"[^"]*"'), r'\1"***"'),
    (re.compile(r'("api_key"\s*:\s*)"[^"]*"'), r'\1"***"'),
    (re.compile(r'("secret"\s*:\s*)"[^"]*"'), r'\1"***"'),
    # 手机号脱敏：138****0001
    (re.compile(r'(1[3-9]\d)\d{4}(\d{4})'), r'\1****\2'),
    # Bearer token 脱敏
    (re.compile(r'(Bearer\s+)\S{10,}'), r'\1***'),
]


class DesensitizeFilter(logging.Filter):
    """日志脱敏过滤器"""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = desensitize(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: desensitize(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    desensitize(str(a)) if isinstance(a, str) else a
                    for a in record.args
                )
        return True


def desensitize(text: str) -> str:
    """对文本进行脱敏处理"""
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def setup_logging(debug: bool = False) -> None:
    """配置应用日志"""
    level = logging.DEBUG if debug else logging.INFO

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(DesensitizeFilter())

    root = logging.getLogger()
    root.setLevel(level)
    # 清除已有的 handler 避免重复
    root.handlers.clear()
    root.addHandler(handler)

    # 降低第三方库日志级别
    for name in ("sqlalchemy.engine", "httpcore", "httpx", "uvicorn.access",
                 "aiosqlite", "asyncio"):
        logging.getLogger(name).setLevel(logging.WARNING)
