from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Float,
    Text,
    DECIMAL,
    JSON,
    TIMESTAMP,
    ForeignKey,
    DateTime,
    Enum as SAEnum,
    text,
    Date,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy.sql import func
from app.db.base import Base
from typing import Optional, List
from app.schemas.enums import AnimalSource, AnimalStatus, OrderStatus


# class Animal moved to app.models.common
class Animal(Base):
    __tablename__ = "animals"
    __table_args__ = (
        UniqueConstraint("sku", "created_by", name="uq_animals_sku_created_by"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String(64), nullable=False)
    species = Column(String(64), nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    base_price = Column(DECIMAL(10, 2), nullable=False)
    specs = Column(JSON, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at = Column(
        TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )

    tracking_animals = relationship(
        "Tracking_Animal", back_populates="category", cascade="all, delete-orphan"
    )


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (
        UniqueConstraint(
            "animal_id", "created_by", name="uq_inventory_animal_id_created_by"
        ),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    animal_id = Column(Integer, ForeignKey("animals.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(DECIMAL(10, 2), nullable=True)
    location = Column(String(128), nullable=True)
    status = Column(String(32), nullable=False, default="available")
    specs = Column(JSON, nullable=True)
    created_at = Column(
        TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )

    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    animal = relationship("Animal", backref="inventory_items")


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("email", "created_by", name="uq_customers_email_created_by"),
        UniqueConstraint("phone", "created_by", name="uq_customers_phone_created_by"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100))
    email = Column(String(255), index=True, nullable=False)
    phone = Column(String(50), index=True, nullable=False)
    customer_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at = Column(
        TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        server_default="CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class Address(Base):
    __tablename__ = "addresses"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    label = Column(String(50))
    line1 = Column(String(255), nullable=False)
    line2 = Column(String(255))
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(100), default="", nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default="CURRENT_TIMESTAMP")
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        server_default="CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer = relationship("Customer", backref="addresses")


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint(
            "order_number", "created_by", name="uq_orders_order_number_created_by"
        ),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_number = Column(String(64), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    billing_address_id = Column(Integer, ForeignKey("addresses.id"), nullable=True)
    shipping_address_id = Column(Integer, ForeignKey("addresses.id"), nullable=True)
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    shipping = Column(DECIMAL(10, 2), default=0)
    tax = Column(DECIMAL(10, 2), default=0)
    total = Column(DECIMAL(10, 2), nullable=False)
    order_status = Column(String(32), nullable=False, default="pending")
    placed_at = Column(
        TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    customer = relationship("Customer", backref="orders")
    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(
        BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    animal_id = Column(Integer, ForeignKey("animals.id"), nullable=False)
    inventory_id = Column(BigInteger, ForeignKey("inventory.id"), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    gross_price = Column(DECIMAL(10, 2), nullable=False)
    total_price = Column(DECIMAL(10, 2), nullable=False)
    discount_value = Column(DECIMAL(10, 2), default=0)
    discount_percent = Column(DECIMAL(10, 2), default=0)
    notes = Column(Text)
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    order = relationship("Order", back_populates="items")
    animal = relationship("Animal")
    tracking_animals = relationship("Tracking_Animal", back_populates="order_item")


class Delivery(Base):
    __tablename__ = "deliveries"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    carrier = Column(String(100), nullable=True)
    tracking_number = Column(String(128), nullable=True)
    status = Column(String(32), default="scheduled")
    notes = Column(Text)
    created_at = Column(
        TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        server_default="CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    order = relationship("Order")


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    paid_at = Column(DateTime, nullable=True)
    method = Column(String(50), nullable=True)
    status = Column(String(32), default="pending")
    reference = Column(String(255), nullable=True)
    created_at = Column(
        TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        server_default="CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    order = relationship("Order")


class OrderVerificationToken(Base):
    __tablename__ = "order_verification_tokens"
    __table_args__ = (
        UniqueConstraint(
            "token", "created_by", name="uq_order_verification_tokens_token_created_by"
        ),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    token = Column(String(64), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("animals.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(
        TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    customer = relationship("Customer")
    animal = relationship("Animal")


class PostOffice(Base):
    __tablename__ = "post_offices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    circlename = Column(String(64), nullable=True)
    regionname = Column(String(64), nullable=True)
    divisionname = Column(String(64), nullable=True)
    officename = Column(String(64), nullable=True)
    pincode = Column(String(64), nullable=True)
    officetype = Column(String(64), nullable=True)
    delivery = Column(String(64), nullable=True)
    district = Column(String(64), nullable=False)  # city
    statename = Column(String(64), nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)


# Moved from app.models.tracking_tables.Tracking_Animal
class Tracking_Animal(Base):
    __tablename__ = "animal_tracking"
    __table_args__ = (
        UniqueConstraint(
            "tag_id", "created_by", name="uq_animal_tracking_tag_id_created_by"
        ),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tag_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("animals.id", ondelete="RESTRICT"), nullable=True, index=True
    )
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
    order_item_id: Mapped[int] = mapped_column(
        ForeignKey("order_items.id"), nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    )
    order_status: Mapped[str] = mapped_column(
        SAEnum(
            OrderStatus,
            values_callable=lambda x: [e.value for e in x],
            native_enum=False,
        ),
        default=OrderStatus.PENDING.value,
        nullable=True,
    )
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # ✅ Relationships
    # Using string references with full path to avoid circular imports if needed,
    # but here we use simple strings assuming they will be resolved by SQLAlchemy registry
    # or we might need to update this if they are not found.
    # For now, keeping them as strings.
    events: Mapped[List["AnimalEvent"]] = relationship(
        back_populates="animal",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    inventory_items: Mapped[List["AnimalInventoryMove"]] = relationship(
        back_populates="animal",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    order_item: Mapped["OrderItem"] = relationship(
        back_populates="tracking_animals",
        lazy="selectin",
    )
    # main_animal: Mapped["Animal"] = relationship(
    #     back_populates="tracking_animals",
    #     lazy="selectin",
    # )
    category: Mapped["Animal"] = relationship(
        back_populates="tracking_animals",
        lazy="selectin",
    )

    milk_collections: Mapped[List["MilkCollection"]] = relationship(
        back_populates="animal",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    weight_collections: Mapped[List["WeightCollection"]] = relationship(
        back_populates="animal",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class AnimalEvent(Base):
    __tablename__ = "animal_events"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id: Mapped[int] = mapped_column(primary_key=True, index=True, nullable=False)
    animal_id: Mapped[int] = mapped_column(
        ForeignKey("animal_tracking.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    event_date: Mapped[Optional[Date]] = mapped_column(Date, index=True, nullable=False)
    milk_quantity: Mapped[Optional[float]] = mapped_column(Float, index=True)
    milk_rate: Mapped[Optional[float]] = mapped_column(Float, index=True)
    milk_snf: Mapped[Optional[float]] = mapped_column(Float, index=True)
    milk_fat: Mapped[Optional[float]] = mapped_column(Float, index=True)
    milk_time: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    milk_water: Mapped[Optional[float]] = mapped_column(Float, index=True)
    milk_session: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    total_price: Mapped[Optional[float]] = mapped_column(Float, index=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    animal: Mapped["Tracking_Animal"] = relationship(
        back_populates="events",
        lazy="selectin",
    )


class AnimalInventoryMove(Base):
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

    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    animal: Mapped["Tracking_Animal"] = relationship(
        back_populates="inventory_items",
        lazy="selectin",
    )


class PurchaseRawMaterial(Base):
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

    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class MilkCollection(Base):
    __tablename__ = "milk_collections"
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
    collection_date: Mapped[Optional[Date]] = mapped_column(Date)
    collection_time: Mapped[Optional[str]] = mapped_column(String(50))
    quantity: Mapped[int] = mapped_column(Integer)
    milk_snf: Mapped[Optional[float]] = mapped_column(Float, index=True)
    milk_fat: Mapped[Optional[float]] = mapped_column(Float, index=True)
    milk_water: Mapped[Optional[float]] = mapped_column(Float, index=True)
    milk_session: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    rate: Mapped[float] = mapped_column(Float)
    total_price: Mapped[float] = mapped_column(Float)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    animal: Mapped["Tracking_Animal"] = relationship(
        back_populates="milk_collections",
        lazy="selectin",
    )


class WeightCollection(Base):
    __tablename__ = "weight_collections"
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
    weight_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    weight_unit: Mapped[str] = mapped_column(String(20), nullable=False, default="kg")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    animal: Mapped["Tracking_Animal"] = relationship(
        back_populates="weight_collections",
        lazy="selectin",
    )
