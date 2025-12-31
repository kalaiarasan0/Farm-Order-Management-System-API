from app.db import tracking_engine
from sqlalchemy import inspect


def inspect_tables():
    insp = inspect(tracking_engine)
    tables = insp.get_table_names()
    print("Tables in tracking DB:", tables)

    if "animal_tracking" in tables:
        columns = insp.get_columns("animal_tracking")
        print("Columns in animal_tracking:", [c["name"] for c in columns])
        fks = insp.get_foreign_keys("animal_events")
        print("FKs on animal_events:", fks)


if __name__ == "__main__":
    inspect_tables()
