import uuid
from pydantic import BaseModel, Field, ConfigDict, EmailStr, AnyHttpUrl
from datetime import datetime

class BizBase(BaseModel):
    # Brand
    name: str = Field(..., max_length=150, example="Acme Corp")
    slug: str = Field(..., max_length=180, example="acme-corp")
    tagline: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None)
    cover_image: AnyHttpUrl | None = Field(default=None)

    # Contact (Regex ensures valid Indian format optionally, but length is safer for general inputs)
    phone: str = Field(..., min_length=10, max_length=20, example="+919876543210")
    phone_alt: str | None = Field(default=None, max_length=20)
    whatsapp: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = Field(default=None)
    website: AnyHttpUrl | None = Field(default=None)

    # Location
    address: str = Field(..., example="123 Main Street, Industrial Area")
    landmark: str | None = Field(default=None)
    pincode: str = Field(..., min_length=6, max_length=6, pattern="^[1-9][0-9]{5}$")
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    geohash: str | None = Field(default=None, max_length=12)

    # Links
    city_id: uuid.UUID
    
    # Flexible Data
    social_links: dict[str, AnyHttpUrl] | None = Field(default=None)

    # Flags
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)

class BizCreate(BizBase):
    # Expect a list of Category UUIDs when creating a business
    category_ids: list[uuid.UUID] = Field(default_factory=list, description="List of category UUIDs to associate with this business")

class BizUpdate(BizBase):
    # Expect a list of Category UUIDs when updating a business
    category_ids: list[uuid.UUID] = Field(default_factory=list, description="List of category UUIDs to associate with this business")

class BizResponse(BizBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    # Optional: Include nested categories if needed in the response
    # categories: list[CategoryResponse] = []

    model_config = ConfigDict(from_attributes=True)