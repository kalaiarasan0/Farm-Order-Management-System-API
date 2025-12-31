from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_tracking_db, get_db
from app.schemas.t_animal_move import CreateMovement, MovementResponse, Cronjob
from app.services.t_animal_movement import create_animal_inventory, list_all_inventory, update_inventory_cronjob
from datetime import datetime

router = APIRouter(prefix="/api/v1/track/inventory_animals", tags=['t_inventory_animals'])

@router.post("/create", response_model = MovementResponse)
def create_inventory_endpoint(payload: CreateMovement, db: Session = Depends(get_tracking_db)):
    "Create Animal History to Inventory"

    try:
        inventory = create_animal_inventory(db, payload.dict())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    
    return MovementResponse(
        id = inventory.id,
        animal_id = inventory.animal_id,
        movement_type = inventory.movement_type,
        movement_date = inventory.movement_date,
        notes = inventory.notes,
    )

@router.get("/update_to_inventory_batch", response_model=Cronjob)
def update_to_inventory(main_db: Session = Depends(get_db), tracking_db: Session = Depends(get_tracking_db)):
    "Update Inventory Cronjob"
    try:
        update_inv_cj = update_inventory_cronjob(main_db, tracking_db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=exc)
    return Cronjob(
        run_time = datetime.now(),
        data = update_inv_cj
    )

@router.get("/list", response_model= list[MovementResponse])
def list_all_inventory_movement(limit: int = 50, offset:int = 0, db: Session = Depends(get_tracking_db)):
    "List all Inventory movement"

    try:
        inventories = list_all_inventory(db, limit, offset)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return [MovementResponse(
                id = inventory.id,
                animal_id = inventory.animal_id,
                movement_type = inventory.movement_type,
                movement_date = inventory.movement_date,
                notes = inventory.notes,
            ) for inventory in inventories]
