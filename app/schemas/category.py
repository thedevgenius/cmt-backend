from unittest import skip

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# Shared properties
class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    slug: str = Field(..., max_length=120, description="URL-friendly identifier")
    icon: Optional[str] = Field(None, max_length=255)
    color: Optional[str] = Field(None, max_length=20, pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$", description="Valid Hex Code")
    is_featured: bool = False
    order: int = 0
    parent_id: Optional[UUID] = None
    
    # SEO Fields
    seo_title: Optional[str] = Field(None, max_length=150)
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = Field(None, max_length=255)
    
    is_active: bool = True

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    slug: Optional[str] = Field(None, max_length=120)
    icon: Optional[str] = Field(None, max_length=255)
    color: Optional[str] = Field(None, max_length=20, pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    is_featured: Optional[bool] = None
    order: Optional[int] = None
    parent_id: Optional[UUID] = None
    seo_title: Optional[str] = Field(None, max_length=150)
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None

# Base response without children to prevent infinite recursion in standard lists
class CategoryResponse(CategoryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Tree response for rendering nested menus (e.g., category selection UI)
class CategoryTreeResponse(CategoryResponse):
    children: List["CategoryTreeResponse"] = []

    model_config = ConfigDict(from_attributes=True)

class PaginatedCategoryResponse(BaseModel):
    total: int
    items: List[CategoryResponse]

class CategoryListRequest(BaseModel):
    skip: int = Field(0, ge=0, description="Number of items to skip for pagination")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of items to return")
    search: Optional[str] = Field(None, description="Search term to filter categories by name or slug")
    parent_id: Optional[UUID] = Field(None, description="Fetch children of a specific parent category")
    top_level_only: Optional[bool] = Field(None, description="If True, only returns root categories")
    is_featured: Optional[bool] = Field(None, description="Filter by featured status")