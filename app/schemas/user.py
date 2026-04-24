import enum
from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.user import UserRole


class UserBase(BaseModel):
    phone: str = Field(..., max_length=20, description="Unique phone number")
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    role: UserRole = Field(default=UserRole.USER)


class UserCreate(UserBase):
    password: Optional[str] = Field(None, min_length=8)


class UserUpdate(BaseModel):
    phone: Optional[str] = Field(None, max_length=20)
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    role: Optional[UserRole] = None
    
    # Status flags can be updated by admins
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_blocked: Optional[bool] = None


class UserResponse(BaseModel):
    id: UUID
    phone: str
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: UserRole
    is_active: bool
    is_verified: bool
    is_blocked: bool
    last_login: Optional[datetime] = None


    # Pydantic V2 configuration to read data from SQLAlchemy objects
    model_config = ConfigDict(from_attributes=True)