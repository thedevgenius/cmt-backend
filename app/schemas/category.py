from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# ------------------------------------------------------------------
# 1. Base & CRUD Schemas
# ------------------------------------------------------------------

class CategoryBase(BaseModel):
    # Added validation constraints here so they apply to CategoryCreate as well
    name: str = Field(..., max_length=100)
    slug: str = Field(..., max_length=120)
    icon: Optional[str] = Field(None, max_length=255)
    color: Optional[str] = Field(None, max_length=20, pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    is_featured: bool = False
    order: int = 0
    is_active: bool = True
    
    # Moved from CategoryUpdate: You need these in Base so they can be set during Creation
    parent_id: Optional[UUID] = None
    seo_title: Optional[str] = Field(None, max_length=150)
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = Field(None, max_length=255)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    # All fields are Optional for PATCH operations
    name: Optional[str] = Field(None, max_length=100)
    slug: Optional[str] = Field(None, max_length=120)
    icon: Optional[str] = Field(None, max_length=255)
    color: Optional[str] = Field(None, max_length=20, pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    is_featured: Optional[bool] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None
    parent_id: Optional[UUID] = None
    seo_title: Optional[str] = Field(None, max_length=150)
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = Field(None, max_length=255)


# ------------------------------------------------------------------
# 2. Response & Request Schemas
# ------------------------------------------------------------------

class CategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    icon: Optional[str] = None
    color: Optional[str] = None
    is_featured: bool
    order: int
    is_active: bool
    parent_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedCategoryResponse(BaseModel):
    total: int
    items: List[CategoryResponse]


class CategoryListRequest(BaseModel):
    skip: int = Field(0, ge=0, description="Number of items to skip for pagination")
    limit: int = Field(30, ge=1, le=1000, description="Maximum number of items to return")
    search: Optional[str] = Field(None, description="Search term to filter categories by name or slug")
    parent_id: Optional[UUID] = Field(None, description="Fetch children of a specific parent category")
    top_level_only: Optional[bool] = Field(None, description="If True, only returns root categories")
    is_featured: Optional[bool] = Field(None, description="Filter by featured status")


# ------------------------------------------------------------------
# 3. Tree Responses
# ------------------------------------------------------------------

# Infinite depth tree (Self-referencing)
class CategoryTreeResponse(CategoryResponse):
    # Note: "children" is grammatically correct, but kept as "childrens" to match your DB relationship
    childrens: List["CategoryTreeResponse"] = Field(default_factory=list)


# Fixed 3-level tree (Cleaned up inheritance and model configs)
class TreeBase(BaseModel):
    id: UUID
    name: str
    slug: str
    
    model_config = ConfigDict(from_attributes=True)

class TreeLevel3(TreeBase):
    parent_id: UUID

class TreeLevel2(TreeBase):
    parent_id: UUID
    childrens: List[TreeLevel3] = Field(default_factory=list)

class TreeResponse(TreeBase):
    childrens: List[TreeLevel2] = Field(default_factory=list)