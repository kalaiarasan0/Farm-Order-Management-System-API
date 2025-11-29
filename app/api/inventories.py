from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.inventories import InventoryCreate, InventoryResponse
from app.services.inventories import create_inventory, get_inventory_by_id, get_inventory_by_animal_id, list_inventories, update_inventory_quantity
from app.services.animals import get_animal_by_id


router = APIRouter(prefix="/api/v1/inventories", tags=["inventories"])

@router.post("/create", response_model=InventoryResponse)
def create_inventory_endpoint(payload: InventoryCreate, db: Session = Depends(get_db)):
    """Create a new inventory entry."""
    try:
        inventory = create_inventory(db, payload.dict())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return InventoryResponse(
        id=inventory.id,
        animal_id=inventory.animal_id,
        quantity=inventory.quantity,
        unit_price=float(inventory.unit_price),
        location=inventory.location,
        status=inventory.status,
        specs=inventory.specs,
        created_at=inventory.created_at.isoformat() if getattr(inventory, "created_at", None) is not None else None,
    )

@router.get("/id/{inventory_id}", response_model=InventoryResponse)
def get_inventory_by_id_endpoint(inventory_id: int, db: Session = Depends(get_db)):
    """Get inventory by ID."""

    inventory = get_inventory_by_id(db, inventory_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="inventory not found")

    return InventoryResponse(
        id=inventory.id,
        animal_id=inventory.animal_id,
        quantity=inventory.quantity,
        unit_price=float(inventory.unit_price),
        location=inventory.location,
        status=inventory.status,
        specs=inventory.specs,
        created_at=inventory.created_at.isoformat() if getattr(inventory, "created_at", None) is not None else None,
    )

@router.get("/animal-id/{animal_id}", response_model=list[InventoryResponse])
def get_inventory_by_animal_id_endpoint(animal_id: int, db: Session = Depends(get_db)):
    """Get inventory by animal ID."""

    inventories = get_inventory_by_animal_id(db, animal_id)
    if not inventories:
        raise HTTPException(status_code=404, detail="inventory not found")

    out = []
    for inventory in inventories:
        out.append(InventoryResponse(
            id=inventory.id,
            animal_id=inventory.animal_id,
            quantity=inventory.quantity,
            unit_price=float(inventory.unit_price),
            location=inventory.location,
            status=inventory.status,
            specs=inventory.specs,
            created_at=inventory.created_at.isoformat() if getattr(inventory, "created_at", None) is not None else None,
        ))
    return out

@router.get("/list", response_model=list[InventoryResponse])
def list_inventories_endpoint(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    """List all inventories."""
    try:
        inventories = list_inventories(db, limit, offset)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    # out = []
    # for inventory in inventories:
    #     animal = None
    #     if getattr(inventory, "animal_id", None):
    #         a = inventory.animal_id
    #         animal = {
    #             "id": a.id,
        #         "sku": a.sku,
        #         "species": a.species,
        #         "name": a.name,
        #         "description": a.description,
        #         "base_price": a.base_price,
        #         "specs": a.specs,
        #         "created_at": a.created_at.isoformat() if getattr(a, "created_at", None) is not None else None,
        #         "updated_at": a.updated_at.isoformat() if getattr(a, "updated_at", None) is not None else None,
        #     }
            # animal = get_animal_by_id(db, inventory.animal_id)

        # out.append(InventoryResponse(
        #     id=inventory.id,
        #     animal_id=inventory.animal_id,
        #     quantity=inventory.quantity,
        #     unit_price=float(inventory.unit_price),
        #     location=inventory.location,
        #     status=inventory.status,
        #     specs=inventory.specs,
        #     created_at=inventory.created_at.isoformat() if getattr(inventory, "created_at", None) is not None else None,
        #     updated_at=inventory.updated_at.isoformat() if getattr(inventory, "updated_at", None) is not None else None,
        # ))
    return inventories
 
@router.patch("/update-quantity/{inventory_id}", response_model=InventoryResponse)
def update_inventory_quantity_endpoint(inventory_id: int, delta_quantity: int, db: Session = Depends(get_db)):
    """Update inventory quantity by a delta amount."""

    try:
        inventory = update_inventory_quantity(db, inventory_id, delta_quantity)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return InventoryResponse(
        id=inventory.id,
        animal_id=inventory.animal_id,
        quantity=inventory.quantity,
        unit_price=float(inventory.unit_price),
        location=inventory.location,
        status=inventory.status,
        specs=inventory.specs,
        created_at=inventory.created_at.isoformat() if getattr(inventory, "created_at", None) is not None else None,
    )