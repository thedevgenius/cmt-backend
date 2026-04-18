import uuid
from typing import Optional
from fastapi import HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func

from app.models.category import Category
from app.schemas import category as category_schemas
from app.crud.category import category_crud
# ------------------------------------------------------------------


async def create_category(category_in: category_schemas.CategoryCreate, db: AsyncSession):

    query = select(Category).where(or_(Category.name == category_in.name, Category.slug == category_in.slug))
    result = await db.execute(query)
    existing_category = result.scalars().first()

    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A category with this name or slug already exists."
        )

    # 2. Check if parent_id is valid (if provided)
    if category_in.parent_id:
        parent_result = await db.execute(select(Category).where(Category.id == category_in.parent_id))
        if not parent_result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found."
            )

    # 3. Create and save the new category
    new_category = Category(**category_in.model_dump())
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)

    return new_category

async def update_category(category_id: uuid.UUID, category_in: category_schemas.CategoryUpdate, db: AsyncSession):
    db_category = await category_crud.get(db, id=category_id)

    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found."
        )

    update_data = category_in.model_dump(exclude_unset=True)
    if not update_data:
        return db_category

    if "name" in update_data or "slug" in update_data:
        existing_category = await category_crud.get_by_name_or_slug(db, name=update_data.get("name"), slug=update_data.get("slug"))
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Another category with this name or slug already exists."
            )

    if "parent_id" in update_data and update_data["parent_id"] is not None:
        new_parent_id = update_data["parent_id"]
        
        if new_parent_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A category cannot be its own parent."
            )

        parent_result = await db.execute(select(Category).where(Category.id == new_parent_id))
        if not parent_result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found."
            )

    for field, value in update_data.items():
        setattr(db_category, field, value)

    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)

    return db_category

async def list_all_categories(
    db: AsyncSession, 
    category_in: category_schemas.CategoryListRequest
) -> list[Category]:
    query = select(Category)
    
    if category_in.search:
        query = query.where(or_(Category.name.ilike(f"%{category_in.search}%"), Category.slug.ilike(f"%{category_in.search}%")))

    if category_in.parent_id is not None:
        query = query.where(Category.parent_id == category_in.parent_id)

    if category_in.top_level_only:
        query = query.where(Category.parent_id == None)

    if category_in.is_featured is not None:
        query = query.where(Category.is_featured == category_in.is_featured)
    
    query = query.offset(category_in.skip).limit(category_in.limit)
    result = await db.execute(query)

    total = await db.execute(select(func.count(Category.id)))
    total = total.scalar()

    return category_schemas.PaginatedCategoryResponse(total=total, items=result.scalars().all())