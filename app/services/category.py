import uuid
from typing import Optional
from fastapi import HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func

from app.models.category import Category
from app.schemas import category as category_schemas
# Assuming your BaseService is imported from something like this:
from app.services.base import BaseService 

class CategoryService(BaseService[Category, category_schemas.CategoryCreate, category_schemas.CategoryUpdate]):
    
    async def create_category(
        self, db: AsyncSession, *, category_in: category_schemas.CategoryCreate
    ) -> Category:
        # 1. Check if category with name or slug already exists
        query = select(Category).where(
            or_(Category.name == category_in.name, Category.slug == category_in.slug)
        )
        result = await db.execute(query)
        
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A category with this name or slug already exists."
            )

        # 2. Check if parent_id is valid (using the inherited get method)
        if category_in.parent_id:
            parent = await self.get(db, id=category_in.parent_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent category not found."
                )

        # 3. Use the inherited BaseService create method to handle db.add, commit, and refresh
        return await super().create(db, obj_in=category_in)


    async def update_category(
        self, db: AsyncSession, *, category_id: uuid.UUID, category_in: category_schemas.CategoryUpdate
    ) -> Category:
        # 1. Fetch the existing category
        db_category = await self.get(db, id=category_id)
        if not db_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found."
            )

        update_data = category_in.model_dump(exclude_unset=True)
        if not update_data:
            return db_category

        # 2. Check for name/slug collisions (excluding the current category being updated)
        if "name" in update_data or "slug" in update_data:
            name = update_data.get("name", db_category.name)
            slug = update_data.get("slug", db_category.slug)
            
            query = select(Category).where(
                or_(Category.name == name, Category.slug == slug),
                Category.id != category_id # Don't conflict with itself
            )
            result = await db.execute(query)
            if result.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Another category with this name or slug already exists."
                )

        # 3. Validate new parent_id
        if "parent_id" in update_data and update_data["parent_id"] is not None:
            new_parent_id = update_data["parent_id"]
            
            if new_parent_id == category_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A category cannot be its own parent."
                )

            parent = await self.get(db, id=new_parent_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent category not found."
                )

        # 4. Use the inherited BaseService update method to apply changes and commit
        return await super().update(db, db_obj=db_category, obj_in=category_in)


    async def list_all_categories(
        self, db: AsyncSession, *, request: category_schemas.CategoryListRequest
    ) -> category_schemas.PaginatedCategoryResponse:
        
        # 1. Build the base query
        query = select(Category)
        
        if request.search:
            query = query.where(
                or_(Category.name.ilike(f"%{request.search}%"), Category.slug.ilike(f"%{request.search}%"))
            )

        if request.parent_id is not None:
            query = query.where(Category.parent_id == request.parent_id)

        if request.top_level_only:
            query = query.where(Category.parent_id.is_(None))

        if request.is_featured is not None:
            query = query.where(Category.is_featured == request.is_featured)
        
        # 2. Get the total count based on the FILTERS (Fixing the bug from the original code)
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)

        # 3. Apply pagination and fetch results
        query = query.offset(request.skip).limit(request.limit)
        result = await db.execute(query)
        items = result.scalars().all()

        return category_schemas.PaginatedCategoryResponse(total=total, items=items)

# Instantiate the service to be used in your routers
category_service = CategoryService(Category)