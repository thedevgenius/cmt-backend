import enum, uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.business import Business

# 1. Define the possible roles
class UserRole(str, enum.Enum):
    USER = "user"       # Standard public directory user
    OWNER = "owner"     # Business owner (can manage their own listings)
    STAFF = "staff"     # Internal team member (requires email/password + OTP)
    ADMIN = "admin"     # Superuser (can create other staff)

class User(Base):
    __tablename__ = "users"

    # Core Identifiers
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Staff Authentication Fields
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    password: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # The Role
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, nullable=False)

    # Status Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    businesses: Mapped["Business"] = relationship("Business", back_populates="owner")