import  uuid
from fastapi import APIRouter, HTTPException, status, Query, Depends

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.dependencies import get_db, get_current_admin
from app.models.category import Category
from app.models.user import User
from app.schemas import category as category_schemas
from app.services import category as category_services


router = APIRouter()

@router.post("", response_model=category_schemas.CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_in: category_schemas.CategoryCreate,
    db: AsyncSession = Depends(get_db),
    # Injecting this dependency automatically locks the route to admins/staff
    current_admin: User = Depends(get_current_admin) 
):
    """Create a new directory category. Requires Admin or Staff privileges."""

    # 1. Check if a category with this name or slug already exists
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


@router.patch("/{category_id}", response_model=category_schemas.CategoryResponse)
async def update_category(
    category_id: uuid.UUID,
    category_in: category_schemas.CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin) 
):
    """Update an existing directory category. Requires Admin or Staff privileges."""
    
    updated_category = await category_services.update_category(category_id, category_in, db)
    return updated_category


@router.get("", response_model=category_schemas.PaginatedCategoryResponse)
async def list_categories(
    category_in = Depends(category_schemas.CategoryListRequest),
    db: AsyncSession = Depends(get_db)
):
    """List all directory categories, with optional search filtering."""

    categories = await category_services.list_all_categories(
       category_in=category_in,
       db=db
    )
    return categories