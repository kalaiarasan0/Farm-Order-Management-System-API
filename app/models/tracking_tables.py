from sqlalchemy import (
    Integer,
    String,
    Date,
    Float,
    ForeignKey,
    DateTime,
    Text,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, mapped_column, Mapped
from typing import Optional
from app.db import TrackingBase
from app.models.common import Tracking_Animal

# class Tracking_Animal moved to app.models.common


class AnimalEvent(TrackingBase):
    __tablename__ = "animal_events"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id: Mapped[int] = mapped_column(primary_key=True)
    animal_id: Mapped[int] = mapped_column(
        ForeignKey("animal_tracking.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(String(50))
    event_date: Mapped[Optional[Date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    )

    animal: Mapped["Tracking_Animal"] = relationship(
        back_populates="events",
        lazy="selectin",
    )


class AnimalInventoryMove(TrackingBase):
    __tablename__ = "animal_inventory_moves"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id: Mapped[int] = mapped_column(primary_key=True)
    animal_id: Mapped[int] = mapped_column(
        ForeignKey("animal_tracking.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    is_move_to_inventory: Mapped[int] = mapped_column(Integer)
    movement_type: Mapped[str] = mapped_column(String(50))
    movement_date: Mapped[Optional[Date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False
    )

    animal: Mapped["Tracking_Animal"] = relationship(
        back_populates="inventory_items",
        lazy="selectin",
    )


class PurchaseRawMaterial(TrackingBase):
    __tablename__ = "purchase_raw_materials"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id: Mapped[int] = mapped_column(primary_key=True)
    material_name: Mapped[str] = mapped_column(Text)
    type_of_material: Mapped[str] = mapped_column(Text)  # feed, medicine, etc
    purchase_date: Mapped[Optional[Date]] = mapped_column(Date)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Float)
    material_expiry_date: Mapped[Optional[Date]] = mapped_column(Date)
    batch_number: Mapped[Optional[str]] = mapped_column(Text)
    supplier: Mapped[Optional[str]] = mapped_column(Text)
    total_price: Mapped[float] = mapped_column(Float)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    gross_price: Mapped[float] = mapped_column(Float)
    discount_amount: Mapped[float] = mapped_column(Float)
    discount_percentage: Mapped[float] = mapped_column(Float)
    material_description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False
    )
