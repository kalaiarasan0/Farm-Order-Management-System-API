import sys
import os
from datetime import date
import random
import string

# Ensure we can import app modules
sys.path.append(os.getcwd())

from app.db import (
    SessionLocal,
    TrackingSessionLocal,
    engine,
    tracking_engine,
    TrackingBase,
)
from app.models import Base
from app.models.tables import Animal as Main_Animal, Inventory
from app.models.tracking_tables import Animal as Track_Animal, AnimalInventoryMove
from app.services.t_animal_movement import update_inventory_cronjob
from decimal import Decimal


def setup_test_data(db_main, db_track):
    suffix = "".join(random.choices(string.ascii_lowercase, k=4))
    breed_name = f"TestBreed_{suffix}"

    # 1. Create Main DB Animal with Base Price
    base_price = Decimal("150.50")
    main_animal = Main_Animal(
        sku=f"SKU-{suffix}",
        species=breed_name,
        name=f"Main Animal {suffix}",
        base_price=base_price,
    )
    db_main.add(main_animal)
    db_main.commit()
    db_main.refresh(main_animal)
    print(
        f"Created Main Animal ID: {main_animal.id}, Base Price: {main_animal.base_price}"
    )

    # 2. Create Tracking DB Animals
    ta = Track_Animal(
        tag_id=f"TAG-{suffix}",
        species="SpeciesX",
        breed=breed_name,
        gender="M",
        source="purchase",
        status="alive",
    )
    db_track.add(ta)
    db_track.commit()
    db_track.refresh(ta)

    # 3. Create Inventory Move
    inv_move = AnimalInventoryMove(
        animal_id=ta.id,
        is_move_to_inventory=0,
        movement_type="entry",
        movement_date=date.today(),
        notes="Stock",
    )
    db_track.add(inv_move)
    db_track.commit()

    return main_animal.id, breed_name, 1, base_price


def verify_sync(
    db_main, db_track, main_animal_id, breed_name, expected_count, expected_price
):
    print("Running update_inventory_cronjob...")
    update_inventory_cronjob(db_main, db_track)

    # Check Inventory
    inventory = (
        db_main.query(Inventory).filter(Inventory.animal_id == main_animal_id).first()
    )

    if inventory:
        print(f"Inventory Quantity: {inventory.quantity}")
        print(f"Inventory Unit Price: {inventory.unit_price}")

        if (
            inventory.quantity == expected_count
            and inventory.unit_price == expected_price
        ):
            print("SUCCESS: Quantity AND Unit Price match expected values.")
        else:
            print(
                f"FAILURE: Qty {inventory.quantity} (exp {expected_count}), Price {inventory.unit_price} (exp {expected_price})"
            )
    else:
        print("FAILURE: Inventory record not found.")


def main():
    db_main = SessionLocal()
    db_track = TrackingSessionLocal()

    try:
        main_animal_id, breed_name, expected_count, expected_price = setup_test_data(
            db_main, db_track
        )
        verify_sync(
            db_main,
            db_track,
            main_animal_id,
            breed_name,
            expected_count,
            expected_price,
        )
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db_main.close()
        db_track.close()


if __name__ == "__main__":
    main()
