import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base



class Category(Base):
    __tablename__ = "categories"

    # Core Identifiers
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)

    # UI & Sorting Elements
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True, doc="URL or icon class name")
    color: Mapped[str | None] = mapped_column(String(20), nullable=True, doc="Hex color code, e.g., #00FF00")
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    order: Mapped[int] = mapped_column(Integer, default=0, index=True, doc="Lower numbers appear first")

    # Hierarchy (Self-Referential)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Relationships
    # 'remote_side' is required for SQLAlchemy to understand self-referential foreign keys
    parent: Mapped["Category"] = relationship("Category", remote_side=[id], back_populates="childrens")
    childrens: Mapped[list["Category"]] = relationship("Category", back_populates="parent", cascade="all, delete-orphan")

    # SEO & Metadata
    seo_title: Mapped[str | None] = mapped_column(String(150), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    seo_keywords: Mapped[str | None] = mapped_column(String(255), nullable=True, doc="Comma-separated keywords")

    # Status Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<Category {self.name} (slug={self.slug})>"