from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.animals import AnimalCreate, AnimalResponse
from app.services.animals import create_animal, get_animal_by_id, get_animal_by_name, list_animals

router = APIRouter(prefix="/api/v1/animals", tags=["animals"])


@router.post("/create", response_model=AnimalResponse)
def create_animal_endpoint(payload: AnimalCreate, db: Session = Depends(get_db)):
    """Create a new animal entry."""
    try:
        animal = create_animal(db, payload.dict())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return AnimalResponse(
        id=animal.id,
        sku=animal.sku,
        name=animal.name,
        species=animal.species,
        description=animal.description,
        base_price=float(animal.base_price),
        specs=animal.specs,
        created_at=animal.created_at.isoformat() if getattr(animal, "created_at", None) is not None else None,
    )


@router.get("/id/{animal_id}", response_model=AnimalResponse)
def get_animal_by_id_endpoint(animal_id: int, db: Session = Depends(get_db)):
    """Get animal by ID."""

    animal = get_animal_by_id(db, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="animal not found")

    return AnimalResponse(
        id=animal.id,
        sku=animal.sku,
        name=animal.name,
        species=animal.species,
        description=animal.description,
        base_price=float(animal.base_price),
        specs=animal.specs,
        created_at=animal.created_at.isoformat() if getattr(animal, "created_at", None) is not None else None,        
    )


@router.get("/name-search/{name}", response_model=list[AnimalResponse])
def get_animal_by_name_endpoint(name: str, db: Session = Depends(get_db)):
    """Get animal by name search."""
    animal = get_animal_by_name(db, name)
    if not animal:
        raise HTTPException(status_code=404, detail="animal not found")
    out = []
    for ani in animal:
        out.append(AnimalResponse(
            id=ani.id,
            sku=ani.sku,
            name=ani.name,
            species=ani.species,
            description=ani.description,
            base_price=float(ani.base_price),
            specs=ani.specs,
            created_at=ani.created_at.isoformat() if getattr(ani, "created_at", None) is not None else None,
        ))
    return out


@router.get("/list", response_model=list[AnimalResponse])
def list_animals_endpoint(db: Session = Depends(get_db)):
    """List all animals."""
    animals = list_animals(db)
    out = []
    for ani in animals:
        out.append(AnimalResponse(
            id=ani.id,
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
