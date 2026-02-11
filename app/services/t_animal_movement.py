from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, func, update
from datetime import date

# from app.models.common import Tracking_Animal as Track_Animal
from app.models.tables import (
    Inventory,
    Animal as Main_Animal,
    AnimalInventoryMove,
    Tracking_Animal as Track_Animal,
)
from fastapi import HTTPException
from app.schemas.enums import AnimalStatus
from app.schemas.users import User


async def create_animal_inventory(
    db: AsyncSession, data: dict, current_user: User
) -> AnimalInventoryMove:
    try:
        async with db.begin():
            result = await db.execute(
                select(Track_Animal).filter(Track_Animal.id == data.get("animal_id"))
            )
            animal = result.scalars().first()

            if animal is None:
                raise HTTPException(status_code=404, detail="Animal not found")

            if animal.status.value != AnimalStatus.alive.value:
                raise HTTPException(
                    status_code=400,
                    detail=f"Animal is not in alive status : {animal.status}",
                )

            animal.inventory_moved_date = date.today()
            animal.status = AnimalStatus.in_inventory.value
            animal.updated_at = date.today()
            animal.updated_by = str(current_user.unique_id)

            inv = AnimalInventoryMove(
                animal_id=data.get("animal_id"),
                movement_type=data.get("movement_type"),
                movement_date=date.today(),
                notes=data.get("notes"),
                is_move_to_inventory=0,
                created_by=str(current_user.unique_id),
            )

            db.add(inv)
        # db.begin context manager commits on exit, but refreshing might need active session or specific handling.
        # However, AsyncSession transaction management is slightly different.
        # If we use `async with db.begin():`, it commits at the end.
        # But `db.refresh` needs to be done.
        # Usually it's better to flush inside or refresh after if session is still valid.
        # With async session, after commit, the object is expired.
        # We can refresh it.
        await db.refresh(inv)
        return inv

    except SQLAlchemyError as exc:
        # rollback is automatic in context manager on error, but we catch it here?
        # If we catch, we might need to rollback if not using context manager or if we re-raise.
        # But `async with db.begin()` handles rollback on exception.
        raise HTTPException(status_code=500, detail=str(exc))


async def list_all_inventory(
    db: AsyncSession, current_user:User, limit: int, offset: int
) -> List[AnimalInventoryMove]:
    result = await db.execute(select(AnimalInventoryMove).filter(AnimalInventoryMove.created_by == str(current_user.unique_id)).limit(limit).offset(offset))
    return result.scalars().all()


async def update_inventory_cronjob(
    db_main: AsyncSession, db_track: AsyncSession, current_user: User = None
):
    try:
        # 1. Aggregate counts by category_id from tracking DB
        stmt_count = (
            select(
                Track_Animal.category_id.label("category_id"),
                func.count(AnimalInventoryMove.id).label("inventory_count"),
            )
            .join(AnimalInventoryMove, AnimalInventoryMove.animal_id == Track_Animal.id)
            .where(AnimalInventoryMove.is_move_to_inventory == 0)
            .group_by(Track_Animal.category_id)
        )
        result = await db_track.execute(stmt_count)
        t_inventory_count = result.mappings().all()

        if not t_inventory_count:
            return []

        synced_results = []

        updater_id = str(current_user.unique_id) if current_user else "system"

        for row in t_inventory_count:
            category_id = row.category_id
            count_to_add = row.inventory_count

            # 2. Find corresponding animal in Main DB
            result_main = await db_main.execute(
                select(Main_Animal).filter(Main_Animal.id == category_id)
            )
            main_animal = result_main.scalars().first()

            if not main_animal:
                msg = f"Warning: Main DB Animal not found for ID '{category_id}'. Skipping."
                # print(msg)

                # Update notes for these records
                subq_animals = select(Track_Animal.id).where(
                    Track_Animal.category_id == category_id
                )

                stmt_update_notes = (
                    update(AnimalInventoryMove)
                    .where(AnimalInventoryMove.animal_id.in_(subq_animals))
                    .where(AnimalInventoryMove.is_move_to_inventory == 0)
                    .values(
                        notes=func.concat(
                            func.coalesce(AnimalInventoryMove.notes, ""), " | ", msg
                        ),
                        updated_by=updater_id,
                    )
                )
                await db_track.execute(stmt_update_notes)
                continue

            # 3. Update or Create Inventory record in Main DB
            result_inv = await db_main.execute(
                select(Inventory).filter(Inventory.animal_id == main_animal.id)
            )
            inventory = result_inv.scalars().first()

            if inventory:
                inventory.quantity += count_to_add
                # Update unit_price to match the current base_price of the animal
                inventory.unit_price = main_animal.base_price
                inventory.updated_by = updater_id
            else:
                inventory = Inventory(
                    animal_id=main_animal.id,
                    quantity=count_to_add,
                    status="available",
                    unit_price=main_animal.base_price,
                    created_by=updater_id,
                )
                db_main.add(inventory)

            # 4. Mark tracking records as synced
            # select IDs of animals with this category_id
            subq_animals = select(Track_Animal.id).where(
                Track_Animal.category_id == category_id
            )

            stmt_update = (
                update(AnimalInventoryMove)
                .where(AnimalInventoryMove.animal_id.in_(subq_animals))
                .where(AnimalInventoryMove.is_move_to_inventory == 0)
                .values(
                    is_move_to_inventory=1,
                    updated_at=func.now(),
                    updated_by=updater_id,
                )
            )
            await db_track.execute(stmt_update)

            synced_results.append(
                {
                    "category_id": main_animal.id,
                    "added_count": count_to_add,
                    "animal_name": main_animal.name,
                }
            )

        await db_main.commit()
        await db_track.commit()
        # print("Synced events:", synced_results)
        return synced_results

    except SQLAlchemyError as e:
        await db_track.rollback()
        await db_main.rollback()
        print(f"Error in update_inventory_cronjob: {e}")
        raise


async def list_tracking_animal_in_master_inventory(
    main_db: AsyncSession,
    track_db: AsyncSession,
    inventory_id: int,
    current_user:User,
    offset: int = 0,
    limit: int = 20,
):
    result_inv = await main_db.execute(
        select(Inventory).filter(Inventory.id == inventory_id)
    )
    inventory = result_inv.scalars().first()

    if inventory is None:
        raise HTTPException(status_code=404, detail="Inventory not found")

    stmt = (
        select(
            AnimalInventoryMove.movement_date.label("movement_date"),
            AnimalInventoryMove.movement_type.label("movement_type"),
            AnimalInventoryMove.notes.label("notes"),
            AnimalInventoryMove.is_move_to_inventory.label("is_move_to_inventory"),
            Track_Animal.tag_id.label("tag_id"),
            Track_Animal.id.label("animal_id"),
            Track_Animal.status.label("status"),
        )
        .join(Track_Animal, AnimalInventoryMove.animal_id == Track_Animal.id)
        .filter(Track_Animal.category_id == inventory.animal_id)
        .order_by(AnimalInventoryMove.movement_date.desc())
        .offset(offset)
        .limit(limit)
    )
    result_tracks = await track_db.execute(stmt)
    track_animals = result_tracks.mappings().all()

    stmt_count = (
        select(func.count(AnimalInventoryMove.id))
        .join(Track_Animal, AnimalInventoryMove.animal_id == Track_Animal.id)
        .filter(Track_Animal.category_id == inventory.animal_id)
    )
    result_count = await track_db.execute(stmt_count)
    track_animal_count = result_count.scalar_one()

    return track_animals, track_animal_count


# if __name__ == "__main__":
#     pass
