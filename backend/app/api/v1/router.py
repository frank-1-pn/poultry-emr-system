from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.records import router as records_router
from app.api.v1.soul import router as soul_router
from app.api.v1.upload import router as upload_router
from app.api.v1.ai_models import router as ai_models_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.export import router as export_router
from app.api.v1.farms import router as farms_router
from app.api.v1.search import router as search_router
from app.api.v1.search_config import router as search_config_router
from app.api.v1.statistics import router as statistics_router
from app.api.v1.reminders import router as reminders_router
from app.api.v1.memory import router as memory_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(records_router)
api_router.include_router(admin_router)
api_router.include_router(upload_router)
api_router.include_router(soul_router)
api_router.include_router(ai_models_router)
api_router.include_router(conversations_router)
api_router.include_router(export_router)
api_router.include_router(farms_router)
api_router.include_router(search_router)
api_router.include_router(search_config_router)
api_router.include_router(statistics_router)
api_router.include_router(reminders_router)
api_router.include_router(memory_router)
