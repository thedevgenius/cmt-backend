import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate
from .base import AsyncCRUDBase

class CRUDCategory(AsyncCRUDBase[Category, CategoryCreate, CategoryUpdate]):
    async def get_by_name_or_slug(self, db: AsyncSession, name: Optional[str] = None, slug: Optional[str] = None) -> Optional[Category]:
        if not name and not slug:
            return None
        
        query = select(Category).where(
            and_(
                (Category.name == name) if name else True,
                (Category.slug == slug) if slug else True
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_parent_id(self, db: AsyncSession, parent_id: uuid.UUID) -> List[Category]:
        result = await db.execute(select(Category).where(Category.parent_id == parent_id))
        return result.scalars().all()
    

# Instantiate the object to use throughout the application
category_crud = CRUDCategory(Category)