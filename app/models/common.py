from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DECIMAL,
    JSON,
    TIMESTAMP,
    DateTime,
    Date,
    Float,
    Enum as SAEnum,
    text,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.db import Base, TrackingBase
from app.schemas.enums import AnimalSource, AnimalStatus

if TYPE_CHECKING:
    from app.models.tracking_tables import AnimalEvent, AnimalInventoryMove


# Moved from app.models.tables.Animal
class Animal(Base):
    __tablename__ = "animals"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String(64), unique=True, nullable=False)
    species = Column(String(64), nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    base_price = Column(DECIMAL(10, 2), nullable=False)
    specs = Column(JSON, nullable=True)
    created_at = Column(
        TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )


# Moved from app.models.tracking_tables.Tracking_Animal
class Tracking_Animal(TrackingBase):
    __tablename__ = "animal_tracking"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tag_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    main_animal_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)

    birth_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    purchase_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)

    source: Mapped[str] = mapped_column(
        SAEnum(
            AnimalSource,
            values_callable=lambda x: [e.value for e in x],
            native_enum=False,
        ),
        nullable=False,
    )

    source_reference: Mapped[Optional[str]] = mapped_column(String(100))
    purchase_price: Mapped[Optional[float]] = mapped_column(Float)

    status: Mapped[str] = mapped_column(
        SAEnum(
            AnimalStatus,
            values_callable=lambda x: [e.value for e in x],
            native_enum=False,
        ),
        default=AnimalStatus.alive,
        nullable=False,
    )
    inventory_moved_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    )

    # ✅ Relationships
    # Using string references with full path to avoid circular imports if needed,
    # but here we use simple strings assuming they will be resolved by SQLAlchemy registry
    # or we might need to update this if they are not found.
    # For now, keeping them as strings.
    events: Mapped[List["AnimalEvent"]] = relationship(
        "app.models.tracking_tables.AnimalEvent",
        back_populates="animal",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    inventory_items: Mapped[List["AnimalInventoryMove"]] = relationship(
        "app.models.tracking_tables.AnimalInventoryMove",
        back_populates="animal",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
