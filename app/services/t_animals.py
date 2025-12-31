import random
from sqlalchemy.orm import Session, selectinload
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from app.models.common import Tracking_Animal, Animal


def create_animal(tracking_db: Session, main_db: Session, data: dict) -> Tracking_Animal:
    try:
        animal = main_db.query(Animal).filter(Animal.id == data.get("animal_id")).first()

        if animal is None:
            raise ValueError("Animal not found")

        animal = Tracking_Animal(
            tag_id=generate_tag_id(tracking_db, animal.species, animal.name),
            main_animal_id=data.get("animal_id"),
            gender=data.get("gender"),
            birth_date=data.get("birth_date"),
            purchase_date=data.get("purchase_date"),
            source=data.get("source").value,
            source_reference=data.get("source_reference"),
            purchase_price=data.get("purchase_price"),
            status=data.get("status").value,
        )

        tracking_db.add(animal)
        tracking_db.commit()
        tracking_db.refresh(animal)
        return animal
    except SQLAlchemyError:
        tracking_db.rollback()
        raise


def generate_tag_id(db: Session, species: str, breed: str) -> str:
    prefix = species[0].upper() + breed[0].upper()
    while True:
        unique_number = random.randint(10000000, 99999999)
        new_tag_id = f"{prefix}{unique_number}"

        tag_exist = (
            db.query(Tracking_Animal)
            .filter(Tracking_Animal.tag_id == new_tag_id)
            .first()
        )

        if tag_exist is None:
            return new_tag_id


def update_animal(db: Session, animal_id, data: dict) -> Tracking_Animal:
    animal = db.query(Tracking_Animal).filter(Tracking_Animal.id == animal_id).first()
    if animal is None:
        raise ValueError("Animal not found")

    for field, value in data.items():
        if value is None:
            continue

        if hasattr(animal, field):
            setattr(animal, field, value)

    try:
        db.commit()
        db.refresh(animal)
    except Exception as exc:
        db.rollback()
        raise ValueError(f"Failed to update animal: {str(exc)}")

    return animal


def list_animals(
    db: Session, limit: int = 50, offset: int = 0
) -> List[Tracking_Animal]:
    return (
        db.query(Tracking_Animal)
        .options(
            selectinload(Tracking_Animal.events),
            selectinload(Tracking_Animal.inventory_items),
        )
        .limit(limit)
        .offset(offset)
        .all()
    )
