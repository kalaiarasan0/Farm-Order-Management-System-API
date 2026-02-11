from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_db
from app.schemas.inventories import (
    InventoryCreate,
    InventoryResponse,
    InventoryListResponse,
)
from app.services.inventories import (
    create_inventory,
    get_inventory_by_id,
    get_inventory_by_category_id,
    list_inventories,
    update_inventory_quantity,
    get_inventory_by_category_name,
)

# from app.services.animals import get_animal_by_id
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/v1/inventories", tags=["inventories"])


@router.post("/create", response_model=InventoryResponse)
async def create_inventory_endpoint(
    payload: InventoryCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """Create a new inventory entry."""
    try:
        # MAP category_id -> category_id
        data = payload.dict()
        data["category_id"] = data.pop("category_id")
        inventory = await create_inventory(db, data, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return InventoryResponse(
        inventory_id=inventory.id,
        category_id=inventory.animal_id,
        quantity=inventory.quantity,
        unit_price=float(inventory.unit_price),
        location=inventory.location,
        status=inventory.status,
        specs=inventory.specs,
        created_at=inventory.created_at.isoformat()
        if getattr(inventory, "created_at", None) is not None
        else None,
    )


@router.get("/id/{inventory_id}", response_model=InventoryResponse)
async def get_inventory_by_id_endpoint(
    inventory_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """Get inventory by ID."""

    inventory = await get_inventory_by_id(db, inventory_id, current_user)
    if not inventory:
        raise HTTPException(status_code=404, detail="inventory not found")

    # Manually map animal fields
    animal_data = None
    if inventory.animal:
        animal_data = {
            "category_id": inventory.animal.id,
            "sku": inventory.animal.sku,
            "species": inventory.animal.species,
            "name": inventory.animal.name,
            "description": inventory.animal.description,
            "base_price": float(inventory.animal.base_price)
            if inventory.animal.base_price is not None
            else 0.0,
            "specs": inventory.animal.specs,
            "created_at": inventory.animal.created_at,
            "updated_at": inventory.animal.updated_at,
        }

    return InventoryResponse(
        inventory_id=inventory.id,
        category_id=inventory.animal_id,
        quantity=inventory.quantity,
        unit_price=float(inventory.unit_price)
        if inventory.unit_price is not None
        else 0.0,
        location=inventory.location,
        status=inventory.status,
        specs=inventory.specs,
        created_at=inventory.created_at.isoformat()
        if getattr(inventory, "created_at", None) is not None
        else None,
        category=animal_data,
    )


@router.get("/category/{category_id}", response_model=list[InventoryResponse])
async def get_inventory_by_category_id_endpoint(
    category_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """Get inventory by category_id (category_id)."""

    # Service layer still uses category_id
    inventories = await get_inventory_by_category_id(db, category_id, current_user)
    if not inventories:
        raise HTTPException(status_code=404, detail="inventory not found")

    out = []
    for inventory in inventories:
        # Manually map animal fields
        animal_data = None
        if inventory.animal:
            animal_data = {
                "category_id": inventory.animal.id,
                "sku": inventory.animal.sku,
                "species": inventory.animal.species,
                "name": inventory.animal.name,
                "description": inventory.animal.description,
                "base_price": float(inventory.animal.base_price)
                if inventory.animal.base_price is not None
                else 0.0,
                "specs": inventory.animal.specs,
                "created_at": inventory.animal.created_at,
                "updated_at": inventory.animal.updated_at,
            }

        out.append(
            InventoryResponse(
                inventory_id=inventory.id,
                category_id=inventory.animal_id,
                quantity=inventory.quantity,
                unit_price=float(inventory.unit_price)
                if inventory.unit_price is not None
                else 0.0,
                location=inventory.location,
                status=inventory.status,
                specs=inventory.specs,
                created_at=inventory.created_at.isoformat()
                if getattr(inventory, "created_at", None) is not None
                else None,
                category=animal_data,
            )
        )
    return out


@router.get("/list", response_model=InventoryListResponse)
async def list_inventories_endpoint(
    limit: int = 50, 
    offset: int = 0, 
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """List all inventories."""
    try:
        inventories, count = await list_inventories(db, current_user, limit, offset)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    out = []
    for inventory in inventories:
        # Manually map animal fields to AnimalResponse schema
        animal_data = None
        if inventory.animal:
            animal_data = {
                "category_id": inventory.animal.id,
                "sku": inventory.animal.sku,
                "species": inventory.animal.species,
                "name": inventory.animal.name,
                "description": inventory.animal.description,
                "base_price": float(inventory.animal.base_price)
                if inventory.animal.base_price is not None
                else 0.0,
                "specs": inventory.animal.specs,
                "created_at": inventory.animal.created_at,
                "updated_at": inventory.animal.updated_at,
            }

        out.append(
            InventoryResponse(
                inventory_id=inventory.id,
                category_id=inventory.animal_id,
                quantity=inventory.quantity,
                unit_price=float(inventory.unit_price)
                if inventory.unit_price is not None
                else 0.0,
                location=inventory.location,
                status=inventory.status,
                specs=inventory.specs,
                created_at=inventory.created_at,
                updated_at=inventory.updated_at,
                category=animal_data,
            )
        )
    return InventoryListResponse(data=out, count=count)


@router.patch("/update-quantity/{inventory_id}", response_model=InventoryResponse)
async def update_inventory_quantity_endpoint(
    inventory_id: int,
    delta_quantity: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """Update inventory quantity by a delta amount."""

    try:
        inventory = await update_inventory_quantity(
            db, inventory_id, delta_quantity, current_user
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return InventoryResponse(
        inventory_id=inventory.id,
        category_id=inventory.animal_id,
        quantity=inventory.quantity,
        unit_price=float(inventory.unit_price),
        location=inventory.location,
        status=inventory.status,
        specs=inventory.specs,
        created_at=inventory.created_at.isoformat()
        if getattr(inventory, "created_at", None) is not None
        else None,
    )


@router.get("/category-name/{category_name}", response_model=InventoryListResponse)
async def get_inventory_by_category_name_endpoint(
    category_name: str,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """Get inventory by category name."""

    inventories, count = await get_inventory_by_category_name(db, category_name, current_user)
    if not inventories and count == 0:
        # NOTE: Returning empty list with count 0 instead of 404 might be better for search
        # But keeping 404 for consistent behavior if desired, though usually search returns empty list
        # Returning 404 as per original logic if "not inventories" was the check
        raise HTTPException(status_code=404, detail="inventory not found")

    out = []
    for inventory in inventories:
        # Manually map animal fields
        animal_data = None
        if inventory.animal:
            animal_data = {
                "category_id": inventory.animal.id,
                "sku": inventory.animal.sku,
                "species": inventory.animal.species,
                "name": inventory.animal.name,
                "description": inventory.animal.description,
                "base_price": float(inventory.animal.base_price)
                if inventory.animal.base_price is not None
                else 0.0,
                "specs": inventory.animal.specs,
                "created_at": inventory.animal.created_at,
                "updated_at": inventory.animal.updated_at,
            }

        out.append(
            InventoryResponse(
                inventory_id=inventory.id,
                category_id=inventory.animal_id,
                quantity=inventory.quantity,
                unit_price=float(inventory.unit_price)
                if inventory.unit_price is not None
                else 0.0,
                location=inventory.location,
                status=inventory.status,
                specs=inventory.specs,
                created_at=inventory.created_at.isoformat()
                if getattr(inventory, "created_at", None) is not None
                else None,
                updated_at=inventory.updated_at.isoformat()
                if getattr(inventory, "updated_at", None) is not None
                else None,
                category=animal_data,
            )
        )
    return InventoryListResponse(data=out, count=count)
