import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

try:
    print("Attempting to import app.models.tables...")
    from app.models import tables

    print("Successfully imported app.models.tables")

    print("Attempting to import app.models.tracking_tables...")
    from app.models import tracking_tables

    print("Successfully imported app.models.tracking_tables")

    print("Attempting to import app.models.common...")
    from app.models import common

    print("Successfully imported app.models.common")

    print("ALL IMPORTS SUCCESSFUL")

except ImportError as e:
    print(f"IMPORT ERROR: {e}")
    sys.exit(1)
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)
