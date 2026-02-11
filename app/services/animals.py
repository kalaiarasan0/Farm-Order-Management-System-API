from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from app.models.tables import Animal
from fastapi import HTTPException
from sqlalchemy import select, func
from app.schemas.users import User


async def create_animal(db: AsyncSession, data: dict, current_user: User) -> Animal:
    stmt = select(Animal).filter(
        (Animal.name == data["name"]) | (Animal.species == data["species"])
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        if existing.name == data["name"]:
            raise HTTPException(
                status_code=400, detail="Animal with this name already exists"
            )
        if existing.species == data["species"]:
            raise HTTPException(
                status_code=400, detail="Animal with this species already exists"
            )

    animal = Animal(**data)
    animal.created_by = str(current_user.unique_id)
    db.add(animal)
    await db.commit()
    await db.refresh(animal)
    return animal


async def get_animal_by_id(db: AsyncSession, animal_id: int, current_user: User) -> Optional[Animal]:
    stmt = select(Animal).where(Animal.id == animal_id, Animal.created_by == str(current_user.unique_id))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_animal_by_name(db: AsyncSession, name: str, current_user: User) -> Optional[Animal]:
    pattern = f"%{name}%"
    stmt = select(Animal).filter(Animal.name.ilike(pattern), Animal.created_by == str(current_user.unique_id))
    result = await db.execute(stmt)
    return result.scalars().all()


async def list_animals(
    db: AsyncSession, current_user: User, limit: int = 50, offset: int = 0
) -> list[Animal]:
    stmt = select(Animal).where(Animal.created_by == str(current_user.unique_id)).order_by(Animal.id.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_count_animals(db: AsyncSession, current_user: User) -> int:
    stmt = select(func.count(Animal.id)).where(Animal.created_by == str(current_user.unique_id))
    result = await db.execute(stmt)
    return result.scalar_one()


async def update_animal(db: AsyncSession, data: dict, current_user: User) -> Animal:
    try:
        animal = await db.get(Animal, data["id"])

        if animal is None:
            raise HTTPException(status_code=404, detail="Animal not found")
        for field, value in data.items():
            if value is None:
                continue
            if hasattr(animal, field):
                setattr(animal, field, value)

        animal.updated_by = str(current_user.unique_id)

        await db.commit()
        await db.refresh(animal)
        return animal
    except SQLAlchemyError:
        await db.rollback()
        raise


async def get_animal_lookups(db: AsyncSession, current_user: User) -> dict:
    stmt = select(
        Animal.id.label("category_id"),
        Animal.name,
    ).where(Animal.created_by == str(current_user.unique_id))
    result = await db.execute(stmt)
    return result.all()
