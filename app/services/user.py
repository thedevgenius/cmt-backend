from .base import BaseService
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate, UserUpdate

class UserService(BaseService[User, UserCreate, UserUpdate]):
    async def get_by_phone(self, db: AsyncSession, phone: str) -> User | None:
        result = await db.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

user_service = UserService(User)