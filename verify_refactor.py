import asyncio
from datetime import date
import sys
import os

# Add project root to sys.path to allow imports
sys.path.append(os.getcwd())

from app.models.tables import MilkCollection, AnimalEvent
from app.services.t_animal_event import create_event


# Mock User
class MockUser:
    unique_id = "user123"


# Mock Session
class MockSession:
    def __init__(self):
        self.added = []
        self.committed = False
        self.refreshed = False

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        self.refreshed = True

    async def rollback(self):
        pass


async def test_create_milk_event():
    print("Testing create_event with MILK event type...")
    db = MockSession()
    user = MockUser()
    data = {
        "animal_id": 1,
        "event_type": "milk",
        "event_date": date(2023, 10, 27),
        "event_milk_time": "Morning",
        "event_milk_quantity": 10.5,
        "event_milk_rate": 50.0,
        "event_milk_snf": 8.5,
        "event_milk_fat": 4.5,
        "event_milk_water": 0.5,
        "event_milk_session": "Session 1",
        "notes": "Good yield",
    }

    try:
        result = await create_event(db, data, user)
        # result is MilkCollection instance
        print(f"Result: {result}")
        
        if isinstance(result, MilkCollection):
            print("✅ Success: Result is instance of MilkCollection")
        else:
            print(f"❌ Failure: Result is {type(result)}, expected MilkCollection")

        if len(db.added) == 1 and isinstance(db.added[0], MilkCollection):
            print("✅ Success: MilkCollection added to session")
            added_obj = db.added[0]
            # Verify fields
            if added_obj.quantity == 10.5:
                print("✅ Success: Quantity matches")
            else:
                print(f"❌ Failure: Quantity mismatch: {added_obj.quantity}")

            if added_obj.rate == 50.0:
                print("✅ Success: Rate matches")
            else:
                print(f"❌ Failure: Rate mismatch: {added_obj.rate}")

            expected_total = 10.5 * 50.0
            if added_obj.total_price == expected_total:
                print("✅ Success: Total price matches")
            else:
                print(f"❌ Failure: Total price mismatch: {added_obj.total_price}")

    except Exception as e:
        print(f"❌ Exception in milk event test: {e}")


async def test_create_other_event():
    print("\nTesting create_event with VACCINATION event type...")
    db = MockSession()
    user = MockUser()
    data = {
        "animal_id": 1,
        "event_type": "vaccination",
        "event_date": date(2023, 10, 28),
        "notes": "Routine vaccination",
    }

    try:
        result = await create_event(db, data, user)
        # result is AnimalEvent instance

        if isinstance(result, AnimalEvent):
            print("✅ Success: Result is instance of AnimalEvent")
        else:
            print(f"❌ Failure: Result is {type(result)}, expected AnimalEvent")

        if len(db.added) == 1 and isinstance(db.added[0], AnimalEvent):
            print("✅ Success: AnimalEvent added to session")
            added_obj = db.added[0]
            if added_obj.event_type == "vaccination":
                print("✅ Success: Event type matches")
            else:
                print(f"❌ Failure: Event type mismatch: {added_obj.event_type}")

    except Exception as e:
        print(f"❌ Exception in other event test: {e}")


async def main():
    with open("verification_result.txt", "w", encoding="utf-8") as f:
        sys.stdout = f
        await test_create_milk_event()
        await test_create_other_event()
    # Also print to stderr so we see something in console
    print("Verification complete. Check verification_result.txt", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
