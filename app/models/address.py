import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, JSON, ForeignKey, UUID
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship

from app.db.base import Base

# ==========================================
# STATE MODEL
# ==========================================
class State(Base):
    __tablename__ = "states"

    # Core Identifiers
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(2), unique=True, index=True, nullable=False, doc="2-letter ISO code, e.g., MH")
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)

    # Status Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Relationships
    cities: Mapped[list["City"]] = relationship("City", back_populates="state", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<State {self.name} ({self.code})>"


# ==========================================
# CITY MODEL
# ==========================================
class City(Base):
    __tablename__ = "cities"

    # Core Identifiers
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)

    # Location Data
    pin_code_prefixes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    
    # Classification
    city_tier: Mapped[int] = mapped_column(Integer, index=True, nullable=False, doc="Tier 1, 2, 3, or 4")

    # Foreign Key & Hierarchy (Updated to UUID)
    state_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("states.id", ondelete="CASCADE"), index=True, nullable=False)

    # Status Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Relationships
    state: Mapped["State"] = relationship("State", back_populates="cities")

    def __repr__(self) -> str:
        return f"<City {self.name} (Tier {self.city_tier})>"