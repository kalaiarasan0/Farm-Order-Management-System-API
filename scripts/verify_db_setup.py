import sys
import os

# Ensure app is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import init_db, TrackingBase, engine, tracking_engine
from app.models import Base


def verify_models():
    print("Verifying model registration...")

    # Check Base tables (Main DB)
    base_tables = list(Base.metadata.tables.keys())
    print(f"Main DB Tables (Base): {base_tables}")

    expected_main = [
        "animals",
        "inventory",
        "customers",
        "addresses",
        "orders",
        "order_items",
        "deliveries",
        "payments",
        "order_verification_tokens",
    ]
    missing_main = [t for t in expected_main if t not in base_tables]

    if missing_main:
        print(f"ERROR: Missing main tables: {missing_main}")
    else:
        print("SUCCESS: All main tables registered.")

    # Check TrackingBase tables (Tracking DB)
    tracking_tables = list(TrackingBase.metadata.tables.keys())
    print(f"Tracking DB Tables (TrackingBase): {tracking_tables}")

    expected_tracking = [
        "animals",
        "animal_events",
    ]  # Note: 'animals' is in both but different Base
    # Actually tracking tables are 'animals', 'animal_events' based on tracking_tables.py

    missing_tracking = [t for t in expected_tracking if t not in tracking_tables]

    if missing_tracking:
        print(f"ERROR: Missing tracking tables: {missing_tracking}")
    else:
        print("SUCCESS: All tracking tables registered.")


if __name__ == "__main__":
    verify_models()
