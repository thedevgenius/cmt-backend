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
    current_admin: User = Depends(get_current_admin) 
):
    """Create a new directory category. Requires Admin or Staff privileges."""

    # 1. Check if a category with this name or slug already exists
    category = await category_services.create_category(category_in, db)
    
    return category


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