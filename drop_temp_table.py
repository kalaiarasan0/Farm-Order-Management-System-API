from app.db import tracking_engine
from sqlalchemy import text


def drop_table():
    with tracking_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS animal_tracking"))
        conn.commit()
        print("Dropped animal_tracking table")


if __name__ == "__main__":
    drop_table()
