from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Poultry EMR System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-here-change-in-production"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/poultry_emr"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600

    # Aliyun OSS
    ALIYUN_OSS_ACCESS_KEY_ID: str = ""
    ALIYUN_OSS_ACCESS_KEY_SECRET: str = ""
    ALIYUN_OSS_ENDPOINT: str = "oss-cn-hangzhou.aliyuncs.com"
    ALIYUN_OSS_BUCKET: str = "poultry-emr"
    ALIYUN_OSS_DOMAIN: str = ""
    ALIYUN_OSS_STS_ROLE_ARN: str = ""

    # WeChat Mini Program
    WECHAT_APPID: str = ""
    WECHAT_SECRET: str = ""

    # JWT
    JWT_SECRET_KEY: str = "your-jwt-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # File upload
    MAX_FILE_SIZE_MB: int = 100

    # Master admin
    MASTER_PHONE: str = "13800000000"
    MASTER_USERNAME: str = "admin"

    # AI 模型加密
    AI_ENCRYPTION_SALT: str = "poultry-emr-ai-key"

    # Embedding
    EMBEDDING_PROVIDER: str = "dashscope"  # dashscope / openai
    EMBEDDING_MODEL: str = "text-embedding-v1"
    EMBEDDING_API_KEY: str = ""  # 为空时复用对应提供商的 LLM key
    EMBEDDING_DIMENSIONS: int = 1536

    # Soul 模块
    SOUL_TOKEN_BUDGET: int = 2000
    SOUL_RATIO: float = 0.6  # Soul 占比 60%，Memory 占比 40%
    SOUL_CACHE_TTL: int = 300  # Redis 缓存 5 分钟

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
