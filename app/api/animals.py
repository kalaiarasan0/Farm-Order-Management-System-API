from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_db
from app.schemas.animals import (
    CategoryCreate,
    CategoryResponse,
    CategoryCount,
    CategoryUpdate,
    CategoryLookup,
)
from app.services.animals import (
    create_animal,
    get_animal_by_id,
    get_animal_by_name,
    list_animals,
    get_count_animals,
    update_animal,
    get_animal_lookups,
)
from app.api.auth import get_current_active_user
from typing import List


router = APIRouter(prefix="/api/v1/category", tags=["category"])


@router.post("/create", response_model=CategoryResponse)
async def create_animal_endpoint(
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """Create a new animal entry."""
    try:
        animal = await create_animal(db, payload.dict(), current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return CategoryResponse(
        category_id=animal.id,
        sku=animal.sku,
        name=animal.name,
        species=animal.species,
        description=animal.description,
        base_price=float(animal.base_price),
        specs=animal.specs,
        created_at=animal.created_at.isoformat()
        if getattr(animal, "created_at", None) is not None
        else None,
        updated_at=animal.updated_at.isoformat()
        if getattr(animal, "updated_at", None) is not None
        else None,
    )


@router.get("/id/{category_id}", response_model=CategoryResponse)
async def get_animal_by_id_endpoint(
    category_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """Get animal by ID."""

    animal = await get_animal_by_id(db, category_id, current_user)
    if not animal:
        raise HTTPException(status_code=404, detail="animal not found")

    return CategoryResponse(
        category_id=animal.id,
        sku=animal.sku,
        name=animal.name,
        species=animal.species,
        description=animal.description,
        base_price=float(animal.base_price),
        specs=animal.specs,
        created_at=animal.created_at.isoformat()
        if getattr(animal, "created_at", None) is not None
        else None,
        updated_at=animal.updated_at.isoformat()
        if getattr(animal, "updated_at", None) is not None
        else None,
    )


@router.get("/name-search/{name}", response_model=List[CategoryResponse])
async def get_animal_by_name_endpoint(
    name: str,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """Get animal by name search."""
    animal = await get_animal_by_name(db, name, current_user)
    if not animal:
        raise HTTPException(status_code=404, detail="animal not found")
    out = []
    for ani in animal:
        out.append(
            CategoryResponse(
                category_id=ani.id,
                sku=ani.sku,
                name=ani.name,
                species=ani.species,
                description=ani.description,
                base_price=float(ani.base_price),
                specs=ani.specs,
                created_at=ani.created_at.isoformat()
                if getattr(ani, "created_at", None) is not None
                else None,
                updated_at=ani.updated_at.isoformat()
                if getattr(ani, "updated_at", None) is not None
                else None,
            )
        )
    return out


@router.get("/list", response_model=List[CategoryResponse])
async def list_animals_endpoint(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """List all animals."""
    animals = await list_animals(db, current_user, limit, offset)
    out = []
    for ani in animals:
        out.append(
            CategoryResponse(
                category_id=ani.id,
                sku=ani.sku,
                name=ani.name,
                species=ani.species,
                description=ani.description,
                base_price=float(ani.base_price),
                specs=ani.specs,
                created_at=ani.created_at.isoformat()
                if getattr(ani, "created_at", None) is not None
                else None,
                updated_at=ani.updated_at.isoformat()
                if getattr(ani, "updated_at", None) is not None
                else None,
            )
        )
    return out


@router.get("/count", response_model=CategoryCount)
async def get_count_animals_endpoint(
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """Get count of animals."""
    count = await get_count_animals(db, current_user)
    return CategoryCount(count=count)


@router.patch("/update", response_model=CategoryResponse)
async def update_animal_endpoint(
    payload: CategoryUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """Update an animal."""
    try:
        animal = await update_animal(db, payload.dict(), current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return CategoryResponse(
        category_id=animal.id,
        sku=animal.sku,
        name=animal.name,
        species=animal.species,
        description=animal.description,
        base_price=float(animal.base_price),
        specs=animal.specs,
        created_at=animal.created_at.isoformat()
        if getattr(animal, "created_at", None) is not None
        else None,
        updated_at=animal.updated_at.isoformat()
        if getattr(animal, "updated_at", None) is not None
        else None,
    )


@router.get("/lookups", response_model=List[CategoryLookup])
async def animal_lookups(
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    return await get_animal_lookups(db, current_user)
