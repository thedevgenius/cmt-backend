from unittest import skip

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# Shared properties
class CategoryBase(BaseModel):
    name: str
    slug: str
    icon: Optional[str] = None
    color: Optional[str] = None
    is_featured: bool
    order: int
    is_active: bool

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
    parent_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    # Tells Pydantic to read data even if it is not a dict, but an ORM model
    model_config = ConfigDict(from_attributes=True)

# Tree response for rendering nested menus (e.g., category selection UI)
class CategoryTreeResponse(CategoryResponse):
    # The field name "childrens" must match your SQLAlchemy relationship name exactly.
    # We use a string reference "CategoryTreeResponse" to allow self-referencing.
    childrens: list["CategoryTreeResponse"] = Field(default_factory=list)

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

class TreeBase(BaseModel):
    id: UUID
    name: str
    slug: str

class TreeLevel3(TreeBase):
    parent_id: UUID

    model_config = ConfigDict(from_attributes=True)

class TreeLevel2(TreeBase):
    parent_id: UUID
    childrens: List[TreeLevel3]

    model_config = ConfigDict(from_attributes=True)


class TreeResponse(TreeBase):
    childrens: List[TreeLevel2]

    model_config = ConfigDict(from_attributes=True)