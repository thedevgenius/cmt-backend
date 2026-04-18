from typing import Any, Dict, Optional, Union
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserRole  # Ensure this points to your actual model path
from app.schemas.user import UserCreate, UserUpdate
from .base import AsyncCRUDBase

class CRUDUser(AsyncCRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_phone(self, db: AsyncSession, *, phone: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        create_data = obj_in.model_dump(exclude={"password"})
        
        if obj_in.password:
            # Hash password logic here
            create_data["password"] = f"{obj_in.password}_hashed"
            
        db_obj = User(**create_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        if update_data.get("password"):
            # Hash password logic here
            update_data["password"] = f"{update_data['password']}_hashed"

        # Note the 'await' here since super().update() is now an async method
        return await super().update(db, db_obj=db_obj, obj_in=update_data)

    def is_active(self, user: User) -> bool:
        """Synchronous check since it doesn't query the DB."""
        return user.is_active and not user.is_blocked

    def is_staff_or_admin(self, user: User) -> bool:
        """Synchronous check since it doesn't query the DB."""
        return user.role in [UserRole.STAFF, UserRole.ADMIN]

# Instantiate
user_crud = CRUDUser(User)