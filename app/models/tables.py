from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    DECIMAL,
    JSON,
    TIMESTAMP,
    ForeignKey,
    DateTime,
    text,
)
from sqlalchemy.orm import relationship
from app.models.common import Animal
from app.db import Base

# class Animal moved to app.models.common


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    animal_id = Column(Integer, ForeignKey("animals.id"), nullable=False, unique=True)
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

    animal = relationship("Animal", backref="inventory_items")


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100))
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50), unique=True, index=True, nullable=False)
    created_at = Column(
        TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        server_default="CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
    )


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
    customer = relationship("Customer", backref="addresses")


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_number = Column(String(64), unique=True, nullable=False)
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
    total_price = Column(DECIMAL(10, 2), nullable=False)
    notes = Column(Text)

    order = relationship("Order", back_populates="items")
    animal = relationship("Animal")


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

    order = relationship("Order")


class OrderVerificationToken(Base):
    __tablename__ = "order_verification_tokens"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    token = Column(String(64), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("animals.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(
        TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    customer = relationship("Customer")
    animal = relationship("Animal")
