from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_tracking_db, get_db
from app.schemas.t_animal_event import (
    CreateEvent,
    AnimalEventResponse,
    UpdateAnimalEvent,
    UpdateEventNotes,
)
from app.services.t_animal_event import (
    create_event,
    update_event_all,
    update_event_notes,
    list_events,
    get_animal_event,
    delete_event,
)

router = APIRouter(prefix="/api/v1/track/animal_events", tags=["t_animal_events"])


@router.post("/create", response_model=AnimalEventResponse)
def create_event_endpoint(payload: CreateEvent, db: Session = Depends(get_tracking_db)):
    "Create a new event"
    try:
        event = create_event(db, payload.dict())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return AnimalEventResponse(
        id=event.id,
        animal_id=event.animal_id,
        event_type=event.event_type,
        event_date=event.event_date,
        notes=event.notes,
    )


@router.patch("/update/{event_id}", response_model=AnimalEventResponse)
def update_event_endpoint(
    event_id: int, payload: UpdateAnimalEvent, db: Session = Depends(get_tracking_db)
):
    "Update an existing event"
    try:
        event = update_event_all(db, event_id, payload.dict(exclude_unset=True))
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
def update_event_notes_endpoint(
    event_id: int, notes: UpdateEventNotes, db: Session = Depends(get_tracking_db)
):
    "Update an existing event notes"
    try:
        event = update_event_notes(db, event_id, notes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return AnimalEventResponse(
        id=event.id,
        animal_id=event.animal_id,
        event_type=event.event_type,
        event_date=event.event_date,
        notes=event.notes,
    )


@router.get("/list", response_model=list[AnimalEventResponse])
def list_events_endpoint(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_tracking_db),
    db_main: Session = Depends(get_db),
):
    "List all events"
    try:
        events = list_events(db, db_main, limit, offset)
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
        )
        for event in events
    ]


@router.get("/list/{event_id}", response_model=AnimalEventResponse)
def get_event_endpoint(
    event_id: int,
    db: Session = Depends(get_tracking_db),
    db_main: Session = Depends(get_db),
):
    "Get a specific event"
    try:
        event = get_animal_event(db, db_main, event_id)
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
    )


@router.delete("/delete/{event_id}", response_model=AnimalEventResponse)
def delete_event_endpoint(event_id: int, db: Session = Depends(get_tracking_db)):
    "Delete an existing event"
    try:
        event = delete_event(db, event_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return AnimalEventResponse(
        id=event.id,
        animal_id=event.animal_id,
        event_type=event.event_type,
        event_date=event.event_date,
        notes=event.notes,
    )
