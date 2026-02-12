"""测试日志脱敏功能"""

from app.core.logging_config import desensitize


def test_desensitize_password():
    text = '{"password": "secret123", "username": "admin"}'
    result = desensitize(text)
    assert "secret123" not in result
    assert '"password": "***"' in result
    assert "admin" in result


def test_desensitize_token():
    text = 'Bearer eyJhbGciOiJIUzI1NiJ9.xxxxxxxxxxxx'
    result = desensitize(text)
    assert "eyJhbGciOiJIUzI1NiJ9" not in result
    assert "Bearer ***" in result


def test_desensitize_phone():
    text = "用户手机号 13812345678 已注册"
    result = desensitize(text)
    assert "13812345678" not in result
    assert "138****5678" in result


def test_desensitize_api_key():
    text = '{"api_key": "sk-1234567890abcdef"}'
    result = desensitize(text)
    assert "sk-1234567890abcdef" not in result
    assert '"api_key": "***"' in result


def test_desensitize_preserves_normal_text():
    text = "这是一条正常的日志信息，没有敏感内容"
    result = desensitize(text)
    assert result == text


def test_desensitize_access_key_secret():
    text = '{"access_key_secret": "ABCDEFGHIJKLMNOP"}'
    result = desensitize(text)
    assert "ABCDEFGHIJKLMNOP" not in result
