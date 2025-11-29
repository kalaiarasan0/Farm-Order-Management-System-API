from sqlalchemy.orm import Session
from typing import List

from app.models.tables import Customer


def get_customer_by_id(db: Session, customer_id: int) -> Customer | None:
    return db.get(Customer, customer_id)


def get_customer_by_phone(db: Session, phone: str) -> Customer | None:
    return db.query(Customer).filter(Customer.phone == phone).first()

def get_customer_count(db: Session) -> int:
    return db.query(Customer).count()

def list_customers(db: Session, limit: int = 50, offset: int = 0) -> List[Customer]:
    return db.query(Customer).order_by(Customer.id.desc()).limit(limit).offset(offset).all()


def create_customer(db: Session, data: dict) -> Customer:
    """Create a new customer and return it."""
    cust = Customer(
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        email=data.get("email"),
        phone=data.get("phone"),
    )
    # Avoid starting a nested transaction if the caller already has one.
    if db.in_transaction():
        db.add(cust)
        db.flush()
    else:
        with db.begin():
            db.add(cust)
            db.flush()
    db.refresh(cust)
    return cust


def update_customer(db: Session, customer_id: int, data: dict) -> Customer:
    """Update an existing customer and return it. Raises ValueError if not found."""
    cust = db.get(Customer, customer_id)
    if not cust:
        raise ValueError("customer not found")

    for key in ("first_name", "last_name", "email", "phone"):
        if key in data:
            setattr(cust, key, data[key])

    # Avoid starting a nested transaction if the caller already has one.
    if db.in_transaction():
        db.add(cust)
        db.flush()
    else:
        with db.begin():
            db.add(cust)
            db.flush()

    db.refresh(cust)
    return cust
