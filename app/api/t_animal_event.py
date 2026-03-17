from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_db
from app.schemas.t_animal_event import (
    CreateEvent,
    AnimalEventResponse,
    UpdateAnimalEvent,
    UpdateEventNotes,
    AnimalEventListResponse,
    EventCreateSuccessResponse,
    CreateBulkMilkCollection,
)
from app.services.t_animal_event import (
    create_event,
    create_bulk_milk_collection,
    update_event_all,
    update_event_notes,
    list_events,
    get_animal_event,
    delete_event,
    get_animal_event_by_animal_id,
    get_animal_event_by_filter_milk,
    get_distinct_animal_event_types,
)
from app.api.auth import get_current_active_user

router = APIRouter(prefix="/api/v1/track/animal_events", tags=["t_animal_events"])


@router.post("/create", response_model=EventCreateSuccessResponse)
async def create_event_endpoint(
    payload: CreateEvent,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "Create a new event"
    try:
        await create_event(db, payload.dict(), current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return EventCreateSuccessResponse(message="Event created successfully")


@router.post("/create/bulk_milk", response_model=EventCreateSuccessResponse)
async def create_bulk_milk_collection_endpoint(
    payload: CreateBulkMilkCollection,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """Create a bulk milk collection distributed amongst multiple animals"""
    try:
        await create_bulk_milk_collection(db, payload.dict(), current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return EventCreateSuccessResponse(message="Bulk milk collection created successfully")


@router.patch("/update/{event_id}", response_model=AnimalEventResponse)
async def update_event_endpoint(
    event_id: int,
    payload: UpdateAnimalEvent,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "Update an existing event"
    try:
        event = await update_event_all(
            db, event_id, payload.dict(exclude_unset=True), current_user
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return AnimalEventResponse(
        id=event.id,
        animal_id=event.animal_id,
        event_type=event.event_type,
        event_date=event.event_date,
        notes=event.notes,
    )


@router.patch("/update_notes/{event_id}", response_model=AnimalEventResponse)
async def update_event_notes_endpoint(
    event_id: int,
    notes: UpdateEventNotes,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "Update an existing event notes"
    try:
        event = await update_event_notes(db, event_id, notes, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return AnimalEventResponse(
        id=event.id,
        animal_id=event.animal_id,
        event_type=event.event_type,
        event_date=event.event_date,
        notes=event.notes,
    )


@router.get("/list/milk", response_model=AnimalEventListResponse)
async def get_milk_events_endpoint(
    animal_id: Optional[int] = None,
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """Get all milk events, optionally filtered by animal_id"""
    try:
        events, count = await get_animal_event_by_filter_milk(
            db, animal_id, current_user, offset, limit
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "count": count,
        "events": [
            AnimalEventResponse(
                id=event.id,
                animal_id=event.animal_id,
                animal_tag_id=getattr(event, "animal_tag_id", None),
                event_date=event.collection_date,
                notes=event.notes,
                category_species=getattr(event, "animal_species", None),
                category_name=getattr(event, "animal_name", None),
                event_milk_time=event.collection_time,
                event_milk_quantity=event.quantity,
                event_milk_snf=event.milk_snf,
                event_milk_fat=event.milk_fat,
                event_milk_water=event.milk_water,
                event_milk_rate=event.rate,
                event_milk_session=event.milk_session,
                total_price=event.total_price,
                created_at=event.created_at,
                updated_at=event.updated_at,
            )
            for event in events
        ],
    }


@router.get("/list/event_types", response_model=list[str])
async def get_distinct_animal_event_types_endpoint(
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """Get all distinct event types"""
    try:
        event_types = await get_distinct_animal_event_types(db, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return event_types


@router.get("/list/{event_id}", response_model=AnimalEventResponse)
async def get_event_endpoint(
    event_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "Get a specific event"
    try:
        event = await get_animal_event(db, event_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return AnimalEventResponse(
        id=event.id,
        animal_id=event.animal_id,
        event_type=event.event_type,
        event_date=event.event_date,
        notes=event.notes,
        animal_species=getattr(event, "animal_species", None),
        animal_name=getattr(event, "animal_name", None),
        total_price=event.total_price,
    )


@router.get("/list/animal/{animal_id}", response_model=AnimalEventListResponse)
async def get_event_by_animal_id_endpoint(
    animal_id: int,
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """Get all events for a specific animal"""
    try:
        events, count = await get_animal_event_by_animal_id(
            db, animal_id, current_user, offset, limit
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "count": count,
        "events": [
            AnimalEventResponse(
                id=event.id,
                animal_id=event.animal_id,
                event_type=event.event_type,
                event_date=event.event_date,
                notes=event.notes,
                category_species=getattr(event, "animal_species", None),
                category_name=getattr(event, "animal_name", None),
                event_milk_time=event.milk_time,
                event_milk_quantity=event.milk_quantity,
                event_milk_snf=event.milk_snf,
                event_milk_fat=event.milk_fat,
                event_milk_water=event.milk_water,
                event_milk_rate=event.milk_rate,
                event_milk_session=event.milk_session,
                total_price=event.total_price,
                created_at=event.created_at,
                updated_at=event.updated_at,
            )
            for event in events
        ],
    }


@router.get("/list", response_model=list[AnimalEventResponse])
async def list_events_endpoint(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "List all events"
    try:
        # Passing db_main as both since we are using get_async_db which usually returns single db session.
        # Ideally we should have separate sessions for main and tracking if they are different DBs.
        # But 'get_async_db' returns session bound to the engine.
        # If tracking info and main info are in same DB (or same engine/session config), this is fine.
        events = await list_events(db, current_user, limit, offset)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return [
        AnimalEventResponse(
            id=event.id,
            animal_id=event.animal_id,
            event_type=event.event_type,
            event_date=event.event_date,
            notes=event.notes,
            animal_species=getattr(event, "animal_species", None),
            animal_name=getattr(event, "animal_name", None),
            total_price=event.total_price,
        )
        for event in events
    ]


@router.delete("/delete/{event_id}", response_model=AnimalEventResponse)
async def delete_event_endpoint(
    event_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "Delete an existing event"
    try:
        event = await delete_event(db, event_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return AnimalEventResponse(
        id=event.id,
        animal_id=event.animal_id,
        event_type=event.event_type,
        event_date=event.event_date,
        notes=event.notes,
    )
