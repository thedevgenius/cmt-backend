import  uuid
from fastapi import APIRouter, HTTPException, status, Query, Depends, Response

from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_db, get_current_admin
from app.models.category import Category
from app.models.user import User
from app.schemas import category as category_schemas
from app.services.category import category_service

from app.core.redis_client import redis_client


router = APIRouter()

@router.post("", response_model=category_schemas.CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_in: category_schemas.CategoryCreate,
    db: AsyncSession = Depends(get_db),
    # current_admin: User = Depends(get_current_admin) 
):
    """Create a new directory category. Requires Admin or Staff privileges."""

    # 1. Check if a category with this name or slug already exists
    category = await category_service.create_category(db, category_in=category_in)
    
    return category


@router.patch("/{category_id}", response_model=category_schemas.CategoryResponse)
async def update_category(
    category_id: uuid.UUID,
    category_in: category_schemas.CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin) 
):
    """Update an existing directory category. Requires Admin or Staff privileges."""
    
    updated_category = await category_service.update_category(db, category_id=category_id, category_in=category_in)
    return updated_category


@router.get("", response_model=category_schemas.PaginatedCategoryResponse)
async def list_categories(
    category_in = Depends(category_schemas.CategoryListRequest),
    db: AsyncSession = Depends(get_db)
):
    """List all directory categories, with optional search filtering."""

    categories = await category_service.list_all_categories(
       request=category_in,
       db=db
    )
    return categories


@router.get("/tree")
async def category_tree(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Category)
        .where(Category.parent_id == None)
        # Eager load Level 2, and then Level 3
        .options(
            selectinload(Category.childrens).selectinload(Category.childrens)
        )
        .order_by(Category.order)
    )
    cache_key = "category:tree"

    # Check Redis cache
    cached_categories = await redis_client.get(cache_key)
    if cached_categories:
        print("Cache hit")
        # return cached_categories
        return Response(content=cached_categories, media_type="application/json")
    
    # Fetch the results
    results = await db.execute(stmt)
    root_categories = results.scalars().all()

    adapter = TypeAdapter(list[category_schemas.TreeResponse])
    validated_models = adapter.validate_python(root_categories)
    
    # 5. Dump the validated models to a JSON string (returns bytes, so we decode to str)
    json_data = adapter.dump_json(validated_models).decode("utf-8")

    await redis_client.set("category:tree", json_data, ex=60)

    return Response(content=json_data, media_type="application/json")
    # return json_data