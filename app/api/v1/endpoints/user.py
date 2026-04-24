from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserUpdate, UserResponse
from app.services.user import user_service

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db) 
):
    updated_data = {
        "full_name": update_data.full_name,
        "email": update_data.email,
    }

    await user_service.update(db, db_obj=current_user, obj_in=updated_data)

    return current_user