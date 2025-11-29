from sqlalchemy.orm import Session, joinedload
from typing import Optional
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.models.tables import Inventory, Animal


def create_inventory(db: Session, data: dict) -> Inventory:

    # Validate animal exists
    animal = db.query(Animal).filter(Animal.id == data.get("animal_id")).first()
    if not animal:
        raise HTTPException(status_code=404, detail=f"Animal {data['animal_id']} does not exist")

    # Check existing inventory for animal
    existing = db.query(Inventory).filter(Inventory.animal_id == data["animal_id"]).first()
    if existing:
        raise HTTPException(status_code=400, detail="Inventory already exists for this animal")
    
    inv = Inventory(
        animal_id=data.get("animal_id"),
        quantity=data.get("quantity"),
        unit_price=data.get("unit_price"),
        location=data.get("location"),
        status=data.get("status", "available"),
        specs=data.get("specs"),
    )

    try:
        db.add(inv)
        db.commit()   # This is where UNIQUE constraint error occurs
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Inventory already exists for animal {data.get('animal_id')}"
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )

    db.refresh(inv)
    return inv


def get_inventory_by_id(db: Session, inventory_id: int) -> Optional[Inventory]:
    return db.get(Inventory, inventory_id)

def get_inventory_by_animal_id(db: Session, animal_id: int) -> Optional[Inventory]:
    return db.query(Inventory).filter(Inventory.animal_id == animal_id).all()

def list_inventories(db: Session, limit: int = 50, offset: int = 0) -> list[Inventory]:
    return db.query(Inventory).options(joinedload(Inventory.animal)).order_by(Inventory.id.desc()).limit(limit).offset(offset).all()

def update_inventory_quantity(db: Session, inventory_id: int, delta_quantity: int) -> Inventory:
    inv = db.get(Inventory, inventory_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory not found")

    new_quantity = inv.quantity + delta_quantity
    if new_quantity < 0:
        raise HTTPException(status_code=400, detail="Insufficient inventory quantity")

    inv.quantity = new_quantity
    db.commit()
    db.refresh(inv)
    return inv