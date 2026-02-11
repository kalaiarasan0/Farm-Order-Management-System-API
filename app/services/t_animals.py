import random
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from app.models.tables import Animal, Tracking_Animal, OrderItem, Order
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.users import User
from .users import UPLOAD_DIR, UPLOAD_URL_PREFIX
import os
import shutil
from uuid import uuid4

async def create_animal(
    db: AsyncSession, data: dict, current_user: User
) -> Tracking_Animal:
    try:
        animal = (
            await db.execute(select(Animal).where(Animal.id == data.get("category_id")))
        ).scalar_one_or_none()

        if animal is None:
            raise HTTPException(status_code=404, detail="Animal not found")

        animal = Tracking_Animal(
            tag_id=await generate_tag_id(db, animal.species, animal.name),
            category_id=data.get("category_id"),
            gender=data.get("gender"),
            birth_date=data.get("birth_date"),
            purchase_date=data.get("purchase_date"),
            source=data.get("source").value,
            source_reference=data.get("source_reference"),
            purchase_price=data.get("purchase_price"),
            status=data.get("status").value,
            created_by=str(current_user.unique_id),
        )

        db.add(animal)
        await db.commit()
        await db.refresh(animal)
        return animal
    except SQLAlchemyError:
        await db.rollback()
        raise


async def generate_tag_id(db: AsyncSession, species: str, breed: str) -> str:
    prefix = species[0].upper() + breed[0].upper()
    while True:
        unique_number = random.randint(10000000, 99999999)
        new_tag_id = f"{prefix}{unique_number}"

        tag_exist = (
            await db.execute(
                select(Tracking_Animal).where(Tracking_Animal.tag_id == new_tag_id)
            )
        ).scalar_one_or_none()

        if tag_exist is None:
            return new_tag_id


async def update_animal(
    db: AsyncSession, animal_id, data: dict, current_user: User
) -> dict:
    animal = (
        await db.execute(select(Tracking_Animal).where(Tracking_Animal.id == animal_id))
    ).scalar_one_or_none()

    if animal is None:
        raise HTTPException(status_code=404, detail="Animal not found")

    for field, value in data.items():
        if value is None:
            continue

        if hasattr(animal, field):
            setattr(animal, field, value)

    animal.updated_by = str(current_user.unique_id)

    try:
        await db.commit()
        await db.refresh(animal)
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Failed to update animal: {str(exc)}"
        )

    return {"message": "Animal updated successfully", "animal_id": animal.id}


async def list_animals(db: AsyncSession, current_user:User, limit: int = 50, offset: int = 0) -> List:
    # 1️⃣ Get tracking animals
    tracking_animals = (
        (
            await db.execute(
                select(Tracking_Animal)
                .filter(Tracking_Animal.created_by == str(current_user.unique_id))
                .options(
                    selectinload(Tracking_Animal.events),
                    selectinload(Tracking_Animal.inventory_items),
                )
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )

    if not tracking_animals:
        return []

    # 2️⃣ Collect category_ids
    animal_ids = {ta.category_id for ta in tracking_animals}

    # 3️⃣ Fetch animals from MAIN DB
    animals = (
        await db.execute(
            select(Animal.id, Animal.name).filter(Animal.id.in_(animal_ids))
        )
    ).all()
    # 4️⃣ Build lookup map
    animal_map = {a.id: a.name for a in animals}

    return [
        {
            **ta.__dict__,
            "animal_name": animal_map.get(ta.category_id),
        }
        for ta in tracking_animals
    ]


async def get_animal_by_id(db: AsyncSession, animal_id: int, current_user:User) -> Tracking_Animal:
    ta = (
        await db.execute(
            select(Tracking_Animal)
            .filter(Tracking_Animal.created_by == str(current_user.unique_id))
            .options(
                selectinload(Tracking_Animal.events),
                selectinload(Tracking_Animal.inventory_items),
            )
            .filter(Tracking_Animal.id == animal_id)
        )
    ).scalar_one_or_none()

    if not ta:
        return None

    animal_name = (
        await db.execute(select(Animal.name).filter(Animal.id == ta.category_id))
    ).scalar_one_or_none()

    return {
        **ta.__dict__,
        "category_name": animal_name,
    }


async def get_animal_by_tag_id(db: AsyncSession, tag_id: str, current_user:User) -> Tracking_Animal:
    pattern = f"%{tag_id}%"
    tracking_animals = (
        (
            await db.execute(
                select(Tracking_Animal)
                .filter(Tracking_Animal.created_by == str(current_user.unique_id))
                .options(
                    selectinload(Tracking_Animal.events),
                    selectinload(Tracking_Animal.inventory_items),
                )
                .filter(Tracking_Animal.tag_id.ilike(pattern))
            )
        )
        .scalars()
        .all()
    )

    if not tracking_animals:
        return []

    # 2️⃣ Collect category_ids
    animal_ids = {ta.category_id for ta in tracking_animals}

    # 3️⃣ Fetch animals from MAIN DB
    animals = (
        await db.execute(
            select(Animal.id, Animal.name).filter(Animal.id.in_(animal_ids))
        )
    ).all()
    # 4️⃣ Build lookup map
    animal_map = {a.id: a.name for a in animals}

    return [
        {
            **ta.__dict__,
            "animal_name": animal_map.get(ta.category_id),
        }
        for ta in tracking_animals
    ]


async def get_count_animals(db: AsyncSession, current_user:User) -> int:
    return (await db.execute(select(func.count(Tracking_Animal.id)).filter(Tracking_Animal.created_by == str(current_user.unique_id)))).scalar_one()


async def map_animal_to_order_item(
    db: AsyncSession, animal_id: int, order_item_id: int, current_user:User
):
    animal = (
        await db.execute(
            select(Tracking_Animal).filter(Tracking_Animal.id == animal_id, Tracking_Animal.created_by == str(current_user.unique_id))
        )
    ).scalar_one_or_none()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")

    if animal.order_item_id:
        raise HTTPException(
            status_code=400, detail="Animal already mapped to an order item"
        )

    order_item = (
        await db.execute(select(OrderItem).filter(OrderItem.id == order_item_id))
    ).scalar_one_or_none()
    if not order_item:
        raise HTTPException(status_code=404, detail="Order item not found")

    order = (
        await db.execute(select(Order).filter(Order.id == order_item.order_id))
    ).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not order_item.animal_id == animal.category_id:
        raise HTTPException(status_code=400, detail="Category ID does not match")

    try:
        animal.order_item_id = order_item_id
        animal.order_status = order.order_status
        db.add(animal)
        await db.commit()
        await db.refresh(animal)
        return animal
    except Exception as e:
        await db.rollback()
        raise ValueError(str(e))


async def get_animal_lookup(
    db: AsyncSession,
    current_user: User,
    search: str = "",
    lookup_filter: str = "",
    order_item_id: int = None,
) -> dict:
    query_stmt = select(Tracking_Animal).filter(Tracking_Animal.created_by == str(current_user.unique_id))
    if lookup_filter == "order_item":
        if order_item_id is None:
            raise HTTPException(status_code=400, detail="Order item ID is required")

        order_item = (
            await db.execute(select(OrderItem).filter(OrderItem.id == order_item_id))
        ).scalar_one_or_none()
        if not order_item:
            raise HTTPException(status_code=404, detail="Order item not found")

        # Filter TrackingAnimal by the animal_id (category) from the order item
        query_stmt = query_stmt.filter(
            Tracking_Animal.category_id == order_item.animal_id
        )

    if search:
        pattern = f"%{search}%"
        query_stmt = query_stmt.filter(Tracking_Animal.tag_id.ilike(pattern))

    tracking_animals = (await db.execute(query_stmt)).scalars().all()

    # 2️⃣ Collect category_ids
    animal_ids = {ta.category_id for ta in tracking_animals}

    # 3️⃣ Fetch animals from MAIN DB
    animals = (
        await db.execute(
            select(Animal.id, Animal.name).filter(Animal.id.in_(animal_ids))
        )
    ).all()
    # 4️⃣ Build lookup map
    animal_map = {a.id: a.name for a in animals}

    return [
        {
            "id": ta.id,
            "category_id": ta.category_id,
            "tag_id": ta.tag_id,
            "category_name": animal_map.get(ta.category_id),
        }
        for ta in tracking_animals
    ]


async def delete_animal(db: AsyncSession, animal_id: int, current_user:User):
    animal = (
        await db.execute(
            select(Tracking_Animal).filter(Tracking_Animal.id == animal_id, Tracking_Animal.created_by == str(current_user.unique_id))
        )
    ).scalar_one_or_none()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    await db.delete(animal)
    await db.commit()
    return {"message": "Animal deleted successfully"}


async def remove_mapped_animal(db: AsyncSession, animal_id: int, order_item_id: int, current_user:User):
    animal = (
        await db.execute(
            select(Tracking_Animal).filter(
                Tracking_Animal.id == animal_id,
                Tracking_Animal.order_item_id == order_item_id,
                Tracking_Animal.created_by == str(current_user.unique_id),
            )
        )
    ).scalar_one_or_none()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    animal.order_item_id = None
    animal.order_status = None
    await db.commit()
    await db.refresh(animal)
    return {"message": "Animal un-mapped successfully"}

async def upload_animal_image(db: AsyncSession, animal_id: int, file: UploadFile, current_user:User):
    try: 

        animal = (
            await db.execute(
                select(Tracking_Animal).filter(Tracking_Animal.id == animal_id, Tracking_Animal.created_by == str(current_user.unique_id))
            )
        ).scalar_one_or_none()
        if not animal:
            raise HTTPException(status_code=404, detail="Animal not found")

        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

        ext = os.path.splitext(file.filename)[1].lower()
        filename = f"{animal.tag_id}_{uuid4()}{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        image_url = f"{UPLOAD_URL_PREFIX}/{filename}"
        animal.image_url = image_url
        await db.commit()
        await db.refresh(animal)
        return {"message": "Image uploaded successfully", "image_url": image_url}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Could not upload file: {str(e)}")

# if __name__ == "__main__":
#     from app.db.database import SessionLocal

#     with SessionLocal() as db:
#         print(get_animal_lookup(db, "", "", None))
