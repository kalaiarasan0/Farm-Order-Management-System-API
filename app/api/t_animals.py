from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.db import get_async_db
from app.schemas.t_animals import (
    AnimalCreate,
    AnimalResponse,
    AnimalUpdate,
    AnimalLookupResponse,
)
from app.services.t_animals import (
    create_animal,
    update_animal,
    list_animals,
    get_animal_by_id,
    get_animal_by_tag_id,
    get_count_animals,
    map_animal_to_order_item,
    get_animal_lookup,
    delete_animal,
    remove_mapped_animal,
    upload_animal_image,
)

# from app.schemas.t_animal_event import AnimalEventResponse
# from app.schemas.t_animal_move import MovementResponse
from app.api.auth import get_current_active_user
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/track/animals", tags=["t_animals"])


@router.post("/create", response_model=dict)
async def create_animal_endpoint(
    payload: AnimalCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "Create a new animal entry"
    try:
        animal = await create_animal(db, payload.dict(), current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"message": "Animal created successfully", "animal_id": animal.id}


@router.get("/list", response_model=list[AnimalResponse])
async def list_animals_endpoint(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "List all animals"
    try:
        animals = await list_animals(db, current_user, limit, offset)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return animals


@router.patch("/update/{animal_id}", response_model=dict)
async def update_animal_endpoint(
    animal_id: int,
    payload: AnimalUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "Update an existing animal entry"
    try:
        animal = await update_animal(
            db, animal_id, payload.dict(exclude_unset=True), current_user
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return animal


@router.get("/id/{animal_id}", response_model=AnimalResponse)
async def get_animal_by_id_endpoint(
    animal_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "Get an animal by ID"
    try:
        animal = await get_animal_by_id(db, animal_id, current_user)
        if not animal:
            raise HTTPException(status_code=404, detail="Animal not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return animal


@router.get("/tag-id/{tag_id}", response_model=list[AnimalResponse])
async def get_animal_by_tag_id_endpoint(
    tag_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "Get an animal by tag ID"
    try:
        animals = await get_animal_by_tag_id(db, tag_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return animals


@router.get("/count", response_model=dict)
async def get_count_animals_endpoint(
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """Get the count of animals"""
    try:
        count = await get_count_animals(db, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"count": count}


@router.get("/lookup", response_model=list[AnimalLookupResponse])
async def get_animal_lookup_endpoint(
    search: str = "",
    filter: str = "",
    order_item_id: int = None,
    animal_status: str = "",
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "Get an animal lookup"
    try:
        animals = await get_animal_lookup(
            db, current_user, search, filter, order_item_id, animal_status
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return animals


@router.patch("/map-animal-to-order-item", response_model=dict)
async def map_animal_to_order_item_endpoint(
    animal_id: int,
    order_item_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "Map an animal to an order item"
    try:
        await map_animal_to_order_item(db, animal_id, order_item_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"message": "Animal mapped to order item successfully"}


@router.patch("/un-map-animal-from-order-item", response_model=dict)
async def delete_mapped_animal_endpoint(
    animal_id: int,
    order_item_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "Un-map an animal from an order item"
    try:
        await remove_mapped_animal(db, animal_id, order_item_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"message": "Animal un-mapped from order item successfully"}


@router.delete("/delete/{animal_id}", response_model=dict)
async def delete_animal_endpoint(
    animal_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "Delete an animal"
    try:
        await delete_animal(db, animal_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"message": "Animal deleted successfully"}


@router.post("/upload-image", response_model=dict)
async def upload_animal_image_endpoint(
    animal_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """Upload an image for an animal"""
    try:
        image_url = await upload_animal_image(db, animal_id, file, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return image_url
