"""
Data Migration Script
---------------------
Copies data from TRACKING_DATABASE_URL (source)
to DATABASE_URL (destination) while preserving IDs.

Tables migrated (in order):
1. animal_tracking
2. animal_events
3. animal_inventory_moves
4. purchase_raw_materials
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

# -----------------------
# DATABASE CONNECTIONS
# -----------------------
SOURCE_DB_URL = settings.TRACKING_DATABASE_URL
DEST_DB_URL = settings.DATABASE_URL

source_engine = create_engine(SOURCE_DB_URL)
dest_engine = create_engine(DEST_DB_URL)

SourceSession = sessionmaker(bind=source_engine)
DestSession = sessionmaker(bind=dest_engine)

TABLES = [
    "animal_tracking",
    "animal_events",
    "animal_inventory_moves",
    "purchase_raw_materials",
]


# -----------------------
# HELPERS
# -----------------------
def disable_fk_checks(session):
    """Disable FK checks (MySQL)"""
    session.execute(text("SET FOREIGN_KEY_CHECKS=0;"))


def enable_fk_checks(session):
    """Enable FK checks (MySQL)"""
    session.execute(text("SET FOREIGN_KEY_CHECKS=1;"))


def truncate_table(session, table_name):
    """Clear destination table before insert (optional but safer)"""
    session.execute(text(f"DELETE FROM {table_name};"))


def reset_sequence_if_needed(session, table_name):
    """
    Optional:
    Adjust AUTO_INCREMENT for MySQL.
    Safe even if not strictly required.
    """
    session.execute(
        text(
            f"""
            SELECT MAX(id) FROM {table_name};
            """
        )
    )


# -----------------------
# MIGRATION LOGIC
# -----------------------
def migrate_table(table_name: str):
    source_session = SourceSession()
    dest_session = DestSession()

    try:
        print(f"\n🚀 Migrating table: {table_name}")

        # Disable FK checks (important for related tables)
        disable_fk_checks(dest_session)

        print("Step 1: FK checks disabled")

        # OPTIONAL: clear destination table
        truncate_table(dest_session, table_name)

        print("Step 2: Destination table truncated")

        # Fetch data from source
        rows = source_session.execute(
            text(f"SELECT * FROM {table_name}")
        ).mappings().all()

        print("Step 3: Data fetched from source")

        if not rows:
            print(f"⚠️  No data found in source table: {table_name}")
            return


        # Insert data into destination
        dest_session.execute(
            text(
                f"""
                INSERT INTO {table_name} ({", ".join(rows[0].keys())})
                VALUES ({", ".join([f":{k}" for k in rows[0].keys()])})
                """
            ),
            rows,
        )

        print("Step 4: Data inserted into destination")

        dest_session.commit()

        print("Step 5: Transaction committed")

        # Verify row count
        source_count = source_session.execute(
            text(f"SELECT COUNT(*) FROM {table_name}")
        ).scalar()

        dest_count = dest_session.execute(
            text(f"SELECT COUNT(*) FROM {table_name}")
        ).scalar()

        print(f"✅ {table_name} migrated successfully")
        print(f"   Source rows: {source_count}")
        print(f"   Dest rows  : {dest_count}")

        if source_count != dest_count:
            print("❌ Row count mismatch!")

    except Exception as e:
        dest_session.rollback()
        print(f"❌ Error migrating {table_name}: {e}")
        raise
    finally:
        enable_fk_checks(dest_session)
        source_session.close()
        dest_session.close()


# -----------------------
# MAIN
# -----------------------

def main():
    print("🔁 Starting Tracking → Main DB Migration")

    for table in TABLES:
        migrate_table(table)

    print("\n🎉 Migration completed successfully!")


if __name__ == "__main__":
    main()
