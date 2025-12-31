from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_tracking_db, get_db
from app.schemas.t_animals import AnimalCreate, AnimalResponse, AnimalUpdate
from app.services.t_animals import create_animal, update_animal, list_animals
from app.schemas.t_animal_event import AnimalEventResponse
from app.schemas.t_animal_move import MovementResponse

router = APIRouter(prefix="/api/v1/track/animals", tags=["t_animals"])


@router.post("/create", response_model=AnimalResponse)
def create_animal_endpoint(
    payload: AnimalCreate, tracking_db: Session = Depends(get_tracking_db), main_db: Session = Depends(get_db)
):
    "Create a new animal entry"
    try:
        animal = create_animal(tracking_db, main_db, payload.dict())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return AnimalResponse(
        id=animal.id,
        tag_id=animal.tag_id,
        main_animal_id=animal.main_animal_id,
        gender=animal.gender,
        birth_date=animal.birth_date,
        purchase_date=animal.purchase_date,
        source=animal.source,
        source_reference=animal.source_reference,
        purchase_price=animal.purchase_price,
        status=animal.status,
        created_at=animal.created_at,
    )

@router.get("/list", response_model=list[AnimalResponse])
def list_animals_endpoint(limit: int = 50, offset: int = 0, db: Session = Depends(get_tracking_db)):
    "List all animals"
    try:
        animals = list_animals(db, limit, offset)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    # output = []
    return [AnimalResponse(
        id=animal.id,
        tag_id=animal.tag_id,
        main_animal_id=animal.main_animal_id,
        gender=animal.gender,
        birth_date=animal.birth_date,
        purchase_date=animal.purchase_date,
        source=animal.source,
        source_reference=animal.source_reference,
        purchase_price=animal.purchase_price,
        status=animal.status,
        created_at=animal.created_at,
        updated_at=animal.updated_at,
        events=[AnimalEventResponse(
            id=event.id,
            animal_id=event.animal_id,
            event_type=event.event_type,
            event_date=event.event_date,
            notes=event.notes,
            created_at=event.created_at,
            updated_at=event.updated_at,
        ) for event in animal.events],
        inventory_items=[MovementResponse(
            id=move.id,
            animal_id=move.animal_id,
            movement_type=move.movement_type,
            movement_date=move.movement_date,
            notes=move.notes,
            created_at=move.created_at,
            updated_at=move.updated_at,
        ) for move in animal.inventory_items],
    ) for animal in animals]

@router.patch("/update/{animal_id}", response_model=AnimalResponse)
def update_animal_endpoint(animal_id: int, payload: AnimalUpdate, db: Session = Depends(get_tracking_db)):
    "Update an existing animal entry"
    try:
        animal = update_animal(db, animal_id, payload.dict(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return AnimalResponse(
        id=animal.id,
        tag_id=animal.tag_id,
        main_animal_id=animal.main_animal_id,
        gender=animal.gender,
        birth_date=animal.birth_date,
        purchase_date=animal.purchase_date,
        source=animal.source,
        source_reference=animal.source_reference,
        purchase_price=animal.purchase_price,
        status=animal.status,
        created_at=animal.created_at,
        updated_at=animal.updated_at,
    )
