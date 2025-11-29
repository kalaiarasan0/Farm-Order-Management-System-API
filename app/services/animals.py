from sqlalchemy.orm import Session
from typing import Optional
from app.models.tables import Animal


def create_animal(db: Session, data: dict) -> Animal:
    existing = db.query(Animal).filter(
        (Animal.name == data["name"]) | (Animal.species == data["species"])
    ).first()

    if existing:
        if existing.name == data["name"]:
            raise ValueError("Animal with this name already exists")
        if existing.species == data["species"]:
            raise ValueError("Animal with this species already exists")

    animal = Animal(**data)
    db.add(animal)
    db.commit()
    db.refresh(animal)
    return animal

def get_animal_by_id(db: Session, animal_id: int) -> Optional[Animal]:
    return db.get(Animal, animal_id) 

def get_animal_by_name(db: Session, name: str) -> Optional[Animal]:
    pattern = f"%{name}%"
    return db.query(Animal).filter(Animal.name.ilike(pattern)).all()

def list_animals(db: Session) -> list[Animal]:
    return db.query(Animal).order_by(Animal.id.desc()).all()