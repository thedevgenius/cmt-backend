import enum, uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional

# Define the enum here as well so Pydantic can validate it
class UserRole(str, enum.Enum):
    USER = "user"
    OWNER = "owner"
    STAFF = "staff"
    ADMIN = "admin"


class UserBase(BaseModel):
    phone: str = Field(..., max_length=20, description="Primary identifier for OTP")
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    role: UserRole = UserRole.USER


class UserCreate(UserBase):
    password: Optional[str] = Field(None, min_length=8)


class UserUpdate(BaseModel):
    # phone: Optional[str] = Field(None, max_length=20)
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_blocked: Optional[bool] = None


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    is_verified: bool
    is_blocked: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)