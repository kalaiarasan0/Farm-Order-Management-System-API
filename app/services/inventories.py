from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.models.tables import Inventory, Animal
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.schemas.users import User


async def create_inventory(
    db: AsyncSession, data: dict, current_user: User
) -> Inventory:
    # Validate animal exists
    stmt = select(Animal).filter(Animal.id == data.get("category_id"))
    result = await db.execute(stmt)
    animal = result.scalar_one_or_none()

    if not animal:
        raise HTTPException(
            status_code=404, detail=f"Animal {data['category_id']} does not exist"
        )

    # Check existing inventory for animal
    stmt = select(Inventory).filter(Inventory.animal_id == data["category_id"])
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=400, detail="Inventory already exists for this animal"
        )

    inv = Inventory(
        animal_id=data.get("category_id"),
        quantity=data.get("quantity"),
        unit_price=data.get("unit_price"),
        location=data.get("location"),
        status=data.get("status", "available"),
        specs=data.get("specs"),
        created_by=str(current_user.unique_id),
    )

    try:
        db.add(inv)
        await db.commit()  # This is where UNIQUE constraint error occurs
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Inventory already exists for animal {data.get('category_id')}",
        )
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))

    await db.refresh(inv)
    return inv


async def get_inventory_by_id(
    db: AsyncSession, inventory_id: int, current_user: User
) -> Optional[Inventory]:
    stmt = (
        select(Inventory)
        .options(selectinload(Inventory.animal))
        .where(Inventory.id == inventory_id, Inventory.created_by == str(current_user.unique_id))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_inventory_by_category_id(
    db: AsyncSession, category_id: int, current_user: User
) -> Optional[Inventory]:
    stmt = (
        select(Inventory)
        .options(selectinload(Inventory.animal))
        .filter(Inventory.animal_id == category_id, Inventory.created_by == str(current_user.unique_id))
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_inventory_by_category_name(
    db: AsyncSession, category_name: str, current_user: User
) -> tuple[list[Inventory], int]:
    pattern = f"%{category_name}%"

    query = select(Inventory).join(Inventory.animal).filter(Animal.name.like(pattern), Inventory.created_by == str(current_user.unique_id))

    count_stmt = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_stmt)
    count = count_result.scalar_one()

    stmt = query.options(selectinload(Inventory.animal))
    result = await db.execute(stmt)
    data = result.scalars().all()

    return data, count


async def   list_inventories(
    db: AsyncSession, current_user: User, limit: int = 50, offset: int = 0
) -> tuple[list[Inventory], int]:
    query = select(Inventory).filter(Inventory.created_by == str(current_user.unique_id))

    count_stmt = select(func.count(Inventory.id))
    count_result = await db.execute(count_stmt)
    count = count_result.scalar_one()

    stmt = (
        query.options(selectinload(Inventory.animal))
        .order_by(Inventory.id.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    data = result.scalars().all()

    return data, count


async def update_inventory_quantity(
    db: AsyncSession, inventory_id: int, delta_quantity: int, current_user: User
) -> Inventory:
    inv = await db.get(Inventory, inventory_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory not found")

    new_quantity = inv.quantity + delta_quantity
    if new_quantity < 0:
        raise HTTPException(status_code=400, detail="Insufficient inventory quantity")

    inv.quantity = new_quantity
    inv.updated_by = str(current_user.unique_id)
    await db.commit()
    await db.refresh(inv)
    return inv
