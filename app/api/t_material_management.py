from fastapi import APIRouter, Depends, HTTPException

# from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_db
from app.schemas.t_material_management import (
    CreateMaterial,
    UpdateMaterial,
    MaterialResponse,
)
from app.services.t_material_management import (
    create_purchase_material,
    update_purchase_material,
    list_purchase_materials,
    get_purchase_material,
    delete_purchase_material,
)
from app.api.auth import get_current_active_user

router = APIRouter(prefix="/api/v1/track/material", tags=["t_material_management"])



@router.post("/create", response_model=MaterialResponse)
async def create_material_endpoint(
    payload: CreateMaterial,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "Create a new material entry"
    try:
        material = await create_purchase_material(db, payload.dict(), current_user)
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
async def update_material_endpoint(
    material_id: int,
    payload: UpdateMaterial,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "Update an existing material entry"
    try:
        material = await update_purchase_material(
            db, material_id, payload.dict(exclude_unset=True), current_user
        )
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
async def list_materials_endpoint(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "List all materials"
    try:
        materials = await list_purchase_materials(db, current_user, limit, offset)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return [
        MaterialResponse(
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
        for material in materials
    ]


@router.get("/list/{material_id}", response_model=MaterialResponse)
async def get_material_endpoint(
    material_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "Get a specific material"
    try:
        material = await get_purchase_material(db, material_id, current_user)
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


@router.delete("/delete/{material_id}", response_model=dict)
async def delete_material_endpoint(
    material_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    "Delete a specific material"
    try:
        material = await delete_purchase_material(db, material_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return material
