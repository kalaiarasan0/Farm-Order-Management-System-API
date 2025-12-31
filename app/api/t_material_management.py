from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_tracking_db
from app.schemas.t_material_management import CreateMaterial, UpdateMaterial, MaterialResponse
from app.services.t_material_management import create_purchase_material, update_purchase_material, list_purchase_materials, get_purchase_material, delete_purchase_material

router = APIRouter(prefix="/api/v1/track/material", tags=["t_material_management"])

@router.post("/create", response_model=MaterialResponse)
def create_material_endpoint(payload: CreateMaterial, db: Session = Depends(get_tracking_db)):
    "Create a new material entry"
    try:
        material = create_purchase_material(db, payload.dict())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return MaterialResponse(
        id=material.id,
        material_name=material.material_name,
        type_of_material=material.type_of_material,
        purchase_date=material.purchase_date,
        quantity=material.quantity,
        unit_price=material.unit_price,
        material_expiry_date=material.material_expiry_date,
        material_batch_number=material.batch_number,
        material_supplier=material.supplier,
        material_description=material.material_description,
        total_price=material.total_price,
        notes=material.notes,
        created_at=material.created_at,
        updated_at=material.updated_at,
        gross_price=material.gross_price,
        discount_amount=material.discount_amount,
        discount_percentage=material.discount_percentage,
    )


@router.patch("/update/{material_id}", response_model=MaterialResponse)
def update_material_endpoint(material_id: int, payload: UpdateMaterial, db: Session = Depends(get_tracking_db)):
    "Update an existing material entry"
    try:
        material = update_purchase_material(db, material_id, payload.dict(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return MaterialResponse(
        id=material.id,
        material_name=material.material_name,
        type_of_material=material.type_of_material,
        purchase_date=material.purchase_date,
        quantity=material.quantity,
        unit_price=material.unit_price,
        material_expiry_date=material.material_expiry_date,
        material_batch_number=material.batch_number,
        material_supplier=material.supplier,
        material_description=material.material_description,
        total_price=material.total_price,
        notes=material.notes,
        created_at=material.created_at,
        updated_at=material.updated_at,
        gross_price=material.gross_price,
        discount_amount=material.discount_amount,
        discount_percentage=material.discount_percentage,
    )


@router.get("/list", response_model=list[MaterialResponse])
def list_materials_endpoint(limit: int = 50, offset: int = 0, db: Session = Depends(get_tracking_db)):
    "List all materials"
    try:
        materials = list_purchase_materials(db, limit, offset)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return [MaterialResponse(
        id=material.id,
        material_name=material.material_name,
        type_of_material=material.type_of_material,
        purchase_date=material.purchase_date,
        quantity=material.quantity,
        unit_price=material.unit_price,
        material_expiry_date=material.material_expiry_date,
        material_batch_number=material.batch_number,
        material_supplier=material.supplier,
        material_description=material.material_description,
        total_price=material.total_price,
        notes=material.notes,
        created_at=material.created_at,
        updated_at=material.updated_at,
        gross_price=material.gross_price,
        discount_amount=material.discount_amount,
        discount_percentage=material.discount_percentage,
    ) for material in materials]

@router.get("/list/{material_id}", response_model=MaterialResponse)
def get_material_endpoint(material_id: int, db: Session = Depends(get_tracking_db)):
    "Get a specific material"
    try:
        material = get_purchase_material(db, material_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return MaterialResponse(
        id=material.id,
        material_name=material.material_name,
        type_of_material=material.type_of_material,
        purchase_date=material.purchase_date,
        quantity=material.quantity,
        unit_price=material.unit_price,
        material_expiry_date=material.material_expiry_date,
        material_batch_number=material.batch_number,
        material_supplier=material.supplier,
        material_description=material.material_description,
        total_price=material.total_price,
        notes=material.notes,
        created_at=material.created_at,
        updated_at=material.updated_at,
        gross_price=material.gross_price,
        discount_amount=material.discount_amount,
        discount_percentage=material.discount_percentage,
    )

@router.delete("/delete/{material_id}", response_model=MaterialResponse)
def delete_material_endpoint(material_id: int, db: Session = Depends(get_tracking_db)):
    "Delete a specific material"
    try:
        material = delete_purchase_material(db, material_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return MaterialResponse(
        id=material.id,
        material_name=material.material_name,
        type_of_material=material.type_of_material,
        purchase_date=material.purchase_date,
        quantity=material.quantity,
        unit_price=material.unit_price,
        material_expiry_date=material.material_expiry_date,
        material_batch_number=material.batch_number,
        material_supplier=material.supplier,
        material_description=material.material_description,
        total_price=material.total_price,
        notes=material.notes,
        created_at=material.created_at,
        updated_at=material.updated_at,
        gross_price=material.gross_price,
        discount_amount=material.discount_amount,
        discount_percentage=material.discount_percentage,
    )
