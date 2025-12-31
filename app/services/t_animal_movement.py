from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, func, update
from datetime import date
from app.models.tracking_tables import AnimalInventoryMove
from app.models.common import Tracking_Animal as Track_Animal
from app.models.tables import Inventory, Animal as Main_Animal


def create_animal_inventory(db: Session, data: dict) -> AnimalInventoryMove:
    try:
        with db.begin():
            animal = (
                db.query(Track_Animal)
                .filter(Track_Animal.id == data.get("animal_id"))
                .first()
            )

            if animal is None:
                raise ValueError("Animal not found")

            if animal.status.value == "alive":
                animal.inventory_moved_date = date.today()
                animal.status = "in_inventory"

                inv = AnimalInventoryMove(
                    animal_id=data.get("animal_id"),
                    movement_type=data.get("movement_type"),
                    movement_date=date.today(),
                    notes=data.get("notes"),
                    is_move_to_inventory=0,
                )

                db.add(inv)
            else:
                raise ValueError(f"Animal is not in alive status : {animal.status}")
        db.refresh(inv)
        return inv

    except SQLAlchemyError:
        db.rollback()
        raise


def list_all_inventory(
    db: Session, limit: int, offset: int
) -> List[AnimalInventoryMove]:
    return db.query(AnimalInventoryMove).limit(limit).offset(offset).all()


def update_inventory_cronjob(db_main: Session, db_track: Session):
    try:
        # 1. Aggregate counts by main_animal_id from tracking DB
        stmt_count = (
            select(
                Track_Animal.main_animal_id.label("main_animal_id"),
                func.count(AnimalInventoryMove.id).label("inventory_count"),
            )
            .join(AnimalInventoryMove, AnimalInventoryMove.animal_id == Track_Animal.id)
            .where(AnimalInventoryMove.is_move_to_inventory == 0)
            .group_by(Track_Animal.main_animal_id)
        )
        t_inventory_count = db_track.execute(stmt_count).mappings().all()

        if not t_inventory_count:
            return []

        synced_results = []

        for row in t_inventory_count:
            main_animal_id = row.main_animal_id
            count_to_add = row.inventory_count

            # 2. Find corresponding animal in Main DB
            main_animal = (
                db_main.query(Main_Animal)
                .filter(Main_Animal.id == main_animal_id)
                .first()
            )

            if not main_animal:
                msg = f"Warning: Main DB Animal not found for ID '{main_animal_id}'. Skipping."
                # print(msg)

                # Update notes for these records
                subq_animals = select(Track_Animal.id).where(
                    Track_Animal.main_animal_id == main_animal_id
                )

                stmt_update_notes = (
                    update(AnimalInventoryMove)
                    .where(AnimalInventoryMove.animal_id.in_(subq_animals))
                    .where(AnimalInventoryMove.is_move_to_inventory == 0)
                    .values(
                        notes=func.concat(
                            func.coalesce(AnimalInventoryMove.notes, ""), " | ", msg
                        )
                    )
                )
                db_track.execute(stmt_update_notes)
                continue

            # 3. Update or Create Inventory record in Main DB
            inventory = (
                db_main.query(Inventory)
                .filter(Inventory.animal_id == main_animal.id)
                .first()
            )

            if inventory:
                inventory.quantity += count_to_add
                # Update unit_price to match the current base_price of the animal
                inventory.unit_price = main_animal.base_price
            else:
                inventory = Inventory(
                    animal_id=main_animal.id,
                    quantity=count_to_add,
                    status="available",
                    unit_price=main_animal.base_price,
                )
                db_main.add(inventory)

            # 4. Mark tracking records as synced
            # select IDs of animals with this main_animal_id
            subq_animals = select(Track_Animal.id).where(
                Track_Animal.main_animal_id == main_animal_id
            )

            stmt_update = (
                update(AnimalInventoryMove)
                .where(AnimalInventoryMove.animal_id.in_(subq_animals))
                .where(AnimalInventoryMove.is_move_to_inventory == 0)
                .values(is_move_to_inventory=1, updated_at=func.now())
            )
            db_track.execute(stmt_update)

            synced_results.append(
                {
                    "main_animal_id": main_animal.id,
                    "added_count": count_to_add,
                    "animal_name": main_animal.name,
                }
            )

        db_main.commit()
        db_track.commit()

        return synced_results

    except SQLAlchemyError as e:
        db_track.rollback()
        db_main.rollback()
        print(f"Error in update_inventory_cronjob: {e}")
        raise


if __name__ == "__main__":
    from app.db import SessionLocal, TrackingSessionLocal

    db_main = SessionLocal()
    db_track = TrackingSessionLocal()

    try:
        events = update_inventory_cronjob(db_main, db_track)
        print("Synced events:", events)
    finally:
        db_main.close()
        db_track.close()
