from fastapi import APIRouter
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import user
from app.api.v1.endpoints import location
from app.api.v1.endpoints import category

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(user.router, prefix="/users", tags=["Users"])
api_router.include_router(location.router, prefix="/location", tags=["Location"])
api_router.include_router(category.router, prefix="/categories", tags=["Categories"])