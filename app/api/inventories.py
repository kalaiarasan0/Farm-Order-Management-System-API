from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.inventories import InventoryCreate, InventoryResponse
from app.services.inventories import create_inventory, get_inventory_by_id, get_inventory_by_product_id, list_inventories, update_inventory_quantity
from app.services.animals import get_animal_by_id


router = APIRouter(prefix="/api/v1/inventories", tags=["inventories"])

@router.post("/create", response_model=InventoryResponse)
def create_inventory_endpoint(payload: InventoryCreate, db: Session = Depends(get_db)):
    """Create a new inventory entry."""
    try:
        # MAP product_id -> product_id
        data = payload.dict()
        data['product_id'] = data.pop('product_id')
        inventory = create_inventory(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return InventoryResponse(
        inventory_id=inventory.id,
        product_id=inventory.animal_id,
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

    # Manually map animal fields
    animal_data = None
    if inventory.animal:
        animal_data = {
            "product_id": inventory.animal.id,
            "sku": inventory.animal.sku,
            "species": inventory.animal.species,
            "name": inventory.animal.name,
            "description": inventory.animal.description,
            "base_price": float(inventory.animal.base_price) if inventory.animal.base_price is not None else 0.0,
            "specs": inventory.animal.specs,
            "created_at": inventory.animal.created_at,
            "updated_at": inventory.animal.updated_at,
        }

    return InventoryResponse(
        inventory_id=inventory.id,
        product_id=inventory.animal_id,
        quantity=inventory.quantity,
        unit_price=float(inventory.unit_price) if inventory.unit_price is not None else 0.0,
        location=inventory.location,
        status=inventory.status,
        specs=inventory.specs,
        created_at=inventory.created_at.isoformat() if getattr(inventory, "created_at", None) is not None else None,
        product=animal_data
    )

@router.get("/product/{product_id}", response_model=list[InventoryResponse])
def get_inventory_by_product_id_endpoint(product_id: int, db: Session = Depends(get_db)):
    """Get inventory by product_id (product_id)."""

    # Service layer still uses product_id
    inventories = get_inventory_by_product_id(db, product_id)
    if not inventories:
        raise HTTPException(status_code=404, detail="inventory not found")

    out = []
    for inventory in inventories:
        # Manually map animal fields
        animal_data = None
        if inventory.animal:
            animal_data = {
                "product_id": inventory.animal.id,
                "sku": inventory.animal.sku,
                "species": inventory.animal.species,
                "name": inventory.animal.name,
                "description": inventory.animal.description,
                "base_price": float(inventory.animal.base_price) if inventory.animal.base_price is not None else 0.0,
                "specs": inventory.animal.specs,
                "created_at": inventory.animal.created_at,
                "updated_at": inventory.animal.updated_at,
            }

        out.append(InventoryResponse(
            inventory_id=inventory.id,
            product_id=inventory.animal_id,
            quantity=inventory.quantity,
            unit_price=float(inventory.unit_price) if inventory.unit_price is not None else 0.0,
            location=inventory.location,
            status=inventory.status,
            specs=inventory.specs,
            created_at=inventory.created_at.isoformat() if getattr(inventory, "created_at", None) is not None else None,
            product=animal_data
        ))
    return out

@router.get("/list", response_model=list[InventoryResponse])
def list_inventories_endpoint(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    """List all inventories."""
    try:
        inventories = list_inventories(db, limit, offset)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    
    out = []
    for inventory in inventories:
        # Manually map animal fields to AnimalResponse schema
        animal_data = None
        if inventory.animal:
            animal_data = {
                "product_id": inventory.animal.id,
                "sku": inventory.animal.sku,
                "species": inventory.animal.species,
                "name": inventory.animal.name,
                "description": inventory.animal.description,
                "base_price": float(inventory.animal.base_price) if inventory.animal.base_price is not None else 0.0,
                "specs": inventory.animal.specs,
                "created_at": inventory.animal.created_at,
                "updated_at": inventory.animal.updated_at,
            }

        out.append(InventoryResponse(
            inventory_id=inventory.id,
            product_id=inventory.animal_id,
            quantity=inventory.quantity,
            unit_price=float(inventory.unit_price) if inventory.unit_price is not None else 0.0,
            location=inventory.location,
            status=inventory.status,
            specs=inventory.specs,
            created_at=inventory.created_at,
            updated_at=inventory.updated_at,
            product=animal_data
        ))
    return out

@router.patch("/update-quantity/{inventory_id}", response_model=InventoryResponse)
def update_inventory_quantity_endpoint(inventory_id: int, delta_quantity: int, db: Session = Depends(get_db)):
    """Update inventory quantity by a delta amount."""

    try:
        inventory = update_inventory_quantity(db, inventory_id, delta_quantity)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return InventoryResponse(
        inventory_id=inventory.id,
        product_id=inventory.animal_id,
        quantity=inventory.quantity,
        unit_price=float(inventory.unit_price),
        location=inventory.location,
        status=inventory.status,
        specs=inventory.specs,
        created_at=inventory.created_at.isoformat() if getattr(inventory, "created_at", None) is not None else None,
    )