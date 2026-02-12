import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.api.v1.ws_conversation import router as ws_router
from app.core.config import get_settings
from app.core.database import engine
from app.core.logging_config import setup_logging
from app.core.rate_limit import RateLimitMiddleware
from app.core.redis import redis_client

settings = get_settings()
setup_logging(debug=settings.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: test connections
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        logger.info("数据库连接成功")
    except Exception as e:
        logger.error("数据库连接失败: %s", e)

    try:
        await redis_client.ping()
        logger.info("Redis连接成功")
    except Exception as e:
        logger.warning("Redis连接失败: %s", e)

    yield

    # Shutdown
    await engine.dispose()
    await redis_client.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router)  # WebSocket 路由（路径已含 /api/v1 前缀）


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
