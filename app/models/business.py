import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, Text, Float, JSON, ForeignKey, UUID, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.address import City
from app.models.category import Category
from app.models.user import User

# ==========================================
# ASSOCIATION TABLE (Many-to-Many)
# ==========================================
# Connects Businesses to Multiple Categories
business_category = Table(
    "business_category",
    Base.metadata,
    Column("business_id", UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)

# ==========================================
# BUSINESS MODEL
# ==========================================
class Business(Base):
    __tablename__ = "businesses"

    # 1. Core Identifiers & Brand
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False)
    tagline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, doc="Detailed description/About Us")
    cover_image: Mapped[str | None] = mapped_column(String(255), nullable=True, doc="URL to the cover image")

    # 2. Contact Information
    phone: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    phone_alt: Mapped[str | None] = mapped_column(String(20), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(150), index=True, nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    social_links: Mapped[dict | None] = mapped_column(JSON, nullable=True, doc="e.g., {'facebook': 'url', 'linkedin': 'url'}")

    # 3. Location Data
    address: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    landmark: Mapped[str | None] = mapped_column(String(200), nullable=True)
    pincode: Mapped[str] = mapped_column(String(6), index=True, nullable=False)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    geohash: Mapped[str | None] = mapped_column(String(12), index=True, nullable=True, doc="For fast radial spatial queries")

    # Foreign Key to City
    city_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cities.id", ondelete="RESTRICT"), index=True, nullable=False)

    # 5. Status & Moderation Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True, doc="Has the business owner verified their identity/location?")

    # 6. Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # ==========================================
    # RELATIONSHIPS
    # ==========================================
    city: Mapped["City"] = relationship("City") # Assumes City model exists

    owner: Mapped["User"] = relationship("User", back_populates="businesses")
    
    # Many-to-Many with Category
    categories: Mapped[list["Category"]] = relationship(
        "Category",
        secondary=business_category,
        backref="businesses" # Allows you to query category.businesses
    )

    def __repr__(self) -> str:
        return f"<Business {self.name} (Verified: {self.is_verified})>"