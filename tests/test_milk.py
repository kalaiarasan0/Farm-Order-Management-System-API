import pytest
from httpx import AsyncClient
from app.schemas.t_animal_event import CreateEvent
from app.models.tables import Animal
import datetime


@pytest.mark.asyncio
async def test_get_milk_events(client: AsyncClient, session):
    # Setup: Create a user is tricky if auth is required.
    # Current implementation of get_current_active_user might need override or we need to login.
    # Assuming we can just override get_current_active_user in the test or use a fixture.
    # For now, let's see if we can hit the public endpoints or how auth is handled.
    # "current_user=Depends(get_current_active_user)"

    # We need to override auth dependency for testing
    from app.api.auth import get_current_active_user
    from app.schemas.users import User
    from app.main import app

    mock_user = User(
        id=1,
        email="test@example.com",
        unique_id="user_123",  # Needs to match expected type of created_by which is string
        is_active=True,
        is_superuser=False,
    )

    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    # 1. Create a dummy animal directly in DB (to avoid API complexity)
    animal = Animal(
        sku="SKU123",
        species="Cow",
        name="Bessie",
        base_price=100.0,
        created_by="user_123",
    )
    session.add(animal)
    await session.commit()
    await session.refresh(animal)

    # 2. Add events via API or DB. Let's use DB to be sure.
    from app.models.tables import AnimalEvent, Tracking_Animal

    # Need a tracking animal record linked to the main animal?
    # Service implementation joins AnimalEvent.animal which is Tracking_Animal.
    # So we need Tracking_Animal.

    tracking_animal = Tracking_Animal(
        tag_id="TAG001",
        category_id=animal.id,
        gender="FEMALE",
        source="birth",
        status="alive",
        created_by="user_123",
    )
    session.add(tracking_animal)
    await session.commit()
    await session.refresh(tracking_animal)

    # Create Milk Event
    event1 = AnimalEvent(
        animal_id=tracking_animal.id,
        event_type="Milk",
        event_date=datetime.date.today(),
        notes="Morning milk",
        created_by="user_123",
    )
    session.add(event1)

    # Create Other Event
    event2 = AnimalEvent(
        animal_id=tracking_animal.id,
        event_type="Medical",
        event_date=datetime.date.today(),
        notes="Checkup",
        created_by="user_123",
    )
    session.add(event2)

    await session.commit()

    # 3. Test /list/milk without animal_id
    response = await client.get("/api/v1/track/animal_events/list/milk")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert len(data["events"]) == 1
    assert data["events"][0]["event_type"] == "Milk"
    assert data["events"][0]["notes"] == "Morning milk"

    # 4. Test /list/milk with correct animal_id
    response = await client.get(
        f"/api/v1/track/animal_events/list/milk?animal_id={tracking_animal.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["events"][0]["id"] == event1.id

    # 5. Test /list/milk with incorrect animal_id
    response = await client.get(
        f"/api/v1/track/animal_events/list/milk?animal_id={tracking_animal.id + 999}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert len(data["events"]) == 0
