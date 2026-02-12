"""API Key 加密工具 - 使用 Fernet 对称加密"""

import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import get_settings


def _get_fernet() -> Fernet:
    """从 SECRET_KEY 派生 Fernet 密钥"""
    settings = get_settings()
    # 使用 PBKDF2 从 SECRET_KEY + salt 派生 32 字节密钥
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        settings.SECRET_KEY.encode(),
        settings.AI_ENCRYPTION_SALT.encode(),
        iterations=100_000,
    )
    # Fernet 需要 url-safe base64 编码的 32 字节密钥
    key = base64.urlsafe_b64encode(dk)
    return Fernet(key)


def encrypt_api_key(plaintext: str) -> str:
    """加密 API Key"""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_api_key(ciphertext: str) -> str:
    """解密 API Key"""
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()
