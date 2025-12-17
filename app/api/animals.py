from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.animals import ProductCreate, ProductResponse
from app.services.animals import create_animal, get_animal_by_id, get_animal_by_name, list_animals

router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.post("/create", response_model=ProductResponse)
def create_animal_endpoint(payload: ProductCreate, db: Session = Depends(get_db)):
    """Create a new animal entry."""
    try:
        animal = create_animal(db, payload.dict())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return ProductResponse(
        product_id=animal.id,
        sku=animal.sku,
        name=animal.name,
        species=animal.species,
        description=animal.description,
        base_price=float(animal.base_price),
        specs=animal.specs,
        created_at=animal.created_at.isoformat() if getattr(animal, "created_at", None) is not None else None,
    )


@router.get("/id/{product_id}", response_model=ProductResponse)
def get_animal_by_id_endpoint(product_id: int, db: Session = Depends(get_db)):
    """Get animal by ID."""

    animal = get_animal_by_id(db, product_id)
    if not animal:
        raise HTTPException(status_code=404, detail="animal not found")

    return ProductResponse(
        product_id=animal.id,
        sku=animal.sku,
        name=animal.name,
        species=animal.species,
        description=animal.description,
        base_price=float(animal.base_price),
        specs=animal.specs,
        created_at=animal.created_at.isoformat() if getattr(animal, "created_at", None) is not None else None,        
    )


@router.get("/name-search/{name}", response_model=list[ProductResponse])
def get_animal_by_name_endpoint(name: str, db: Session = Depends(get_db)):
    """Get animal by name search."""
    animal = get_animal_by_name(db, name)
    if not animal:
        raise HTTPException(status_code=404, detail="animal not found")
    out = []
    for ani in animal:
        out.append(ProductResponse(
            product_id=ani.id,
            sku=ani.sku,
            name=ani.name,
            species=ani.species,
            description=ani.description,
            base_price=float(ani.base_price),
            specs=ani.specs,
            created_at=ani.created_at.isoformat() if getattr(ani, "created_at", None) is not None else None,
        ))
    return out


@router.get("/list", response_model=list[ProductResponse])
def list_animals_endpoint(db: Session = Depends(get_db)):
    """List all animals."""
    animals = list_animals(db)
    out = []
    for ani in animals:
        out.append(ProductResponse(
            product_id=ani.id,
            sku=ani.sku,
            name=ani.name,
            species=ani.species,
            description=ani.description,
            base_price=float(ani.base_price),
            specs=ani.specs,
            created_at=ani.created_at.isoformat() if getattr(
                ani, "created_at", None) is not None else None,
        ))
    return out
