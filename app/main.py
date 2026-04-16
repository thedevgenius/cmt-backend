from fastapi import FastAPI

from app.core.config import settings
from app.core.health import router as health_router
from app.api.v1.router import api_router as api_v1_router

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(health_router)
app.include_router(api_v1_router, prefix="/v1")