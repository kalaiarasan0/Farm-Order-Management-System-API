from sqlalchemy.orm import Session, joinedload
from typing import Optional

from app.models.tables import Address


def get_address_by_id(db: Session, address_id: int) -> Optional[Address]:
    return db.get(Address, address_id)


def create_address(db: Session, data: dict) -> Address:
    addr = Address(
        customer_id=data.get("customer_id"),
        label=data.get("label"),
        line1=data.get("line1"),
        line2=data.get("line2"),
        city=data.get("city"),
        state=data.get("state"),
        postal_code=data.get("postal_code"),
        country=data.get("country", ""),
    )
    with db.begin():
        db.add(addr)
        db.flush()

    db.refresh(addr)
    return addr


def update_address(db: Session, address_id: int, data: dict) -> Address:
    addr = db.get(Address, address_id)
    if not addr:
        raise ValueError("address not found")

    for key in ("label", "line1", "line2", "city", "state", "postal_code", "country"):
        if key in data:
            setattr(addr, key, data[key])

    with db.begin():
        db.add(addr)
        db.flush()

    db.refresh(addr)
    return addr


def list_addresses(db: Session) -> list[Address]:
    # eager-load customer to avoid N+1 when returning customer name in API
    return db.query(Address).options(joinedload(Address.customer)).order_by(Address.id.desc()).all()

def list_addresses_by_customer_id(db: Session, customer_id: int) -> list[Address]:
    return (
        db.query(Address)
        .options(joinedload(Address.customer))
        .filter(Address.customer_id == customer_id)
        .order_by(Address.id.desc())
        .all()
    )