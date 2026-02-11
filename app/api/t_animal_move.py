from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_db
from app.schemas.t_animal_move import (
    CreateMovement,
    MovementResponse,
    Cronjob,
    TrackingMovementListResponse,
    TrackingMovementResponse,
)
from app.services.t_animal_movement import (
    create_animal_inventory,
    list_all_inventory,
    update_inventory_cronjob,
    list_tracking_animal_in_master_inventory,
)
from datetime import datetime
from app.api.auth import get_current_active_user

router = APIRouter(
    prefix="/api/v1/track/inventory_animals", tags=["t_inventory_animals"]
)


@router.post("/create", response_model=MovementResponse)
async def create_inventory_endpoint(
    payload: CreateMovement,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    main_db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "Create Animal History to Inventory"

    try:
        inventory = await create_animal_inventory(db, payload.dict(), current_user)
        # To call async function in background task, we can just pass the async function and args.
        # But FastAPI BackgroundTasks in standard way runs synchronous functions in thread pool or async functions in event loop.
        # It handles async def automatically.
        background_tasks.add_task(update_inventory_cronjob, main_db, db, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return MovementResponse(
        id=inventory.id,
        animal_id=inventory.animal_id,
        movement_type=inventory.movement_type,
        movement_date=inventory.movement_date,
        notes=inventory.notes,
    )


@router.get("/update_to_inventory_batch", response_model=Cronjob)
async def update_to_inventory(
    main_db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "Update Inventory Cronjob"
    try:
        # Since update_inventory_cronjob uses two DBs (main_db and db_track)
        # Here we are passing main_db as both? Or should we fix the dependency?
        # The previous code was: update_inventory_cronjob(main_db, main_db)
        # This implies db_track was same as main_db or it was a bug/simplification?
        # Looking at original code: update_inventory_cronjob(db_main, db_track)
        # And endpoint passed main_db for both arguments.
        # This means db_track is same as main_db session?
        # In `app/db/database.py`, there is `get_db` and usually one DB.
        # If the app uses single DB for everything now, then passing main_db twice is correct.
        update_inv_cj = await update_inventory_cronjob(main_db, main_db, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=exc)
    return Cronjob(run_time=datetime.now(), data=update_inv_cj)


@router.get("/list", response_model=list[MovementResponse])
async def list_all_inventory_movement(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "List all Inventory movement"

    try:
        inventories = await list_all_inventory(db, current_user, limit, offset)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return [
        MovementResponse(
            id=inventory.id,
            animal_id=inventory.animal_id,
            movement_type=inventory.movement_type,
            movement_date=inventory.movement_date,
            notes=inventory.notes,
        )
        for inventory in inventories
    ]


@router.get(
    "/list_tracking_animal_in_master_inventory",
    response_model=TrackingMovementListResponse,
)
async def list_tracking_animal_in_master_inventory_endpoint(
    inventory_id: int,
    offset: int = 0,
    limit: int = 20,
    main_db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "List all Inventory movement"

    try:
        # Again passing main_db as both databases
        inventories, count = await list_tracking_animal_in_master_inventory(
            main_db, main_db, inventory_id, current_user, offset, limit
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "data": [
            TrackingMovementResponse.model_validate(
                {
                    **inventory,
                    "status": inventory["status"].value
                    if inventory["status"]
                    else None,
                }
            )
            for inventory in inventories
        ],
        "count": count,
    }
