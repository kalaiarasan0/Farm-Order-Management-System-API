from app.db import tracking_engine
from sqlalchemy import inspect


def inspect_constraints():
    insp = inspect(tracking_engine)
    fks = insp.get_foreign_keys("animal_events")
    print("Foreign Keys on animal_events:")
    for fk in fks:
        print(fk)

    fks_inv = insp.get_foreign_keys("animal_inventory_moves")
    print("Foreign Keys on animal_inventory_moves:")
    for fk in fks_inv:
        print(fk)


if __name__ == "__main__":
    inspect_constraints()
