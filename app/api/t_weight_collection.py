from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_db
from app.schemas.t_weight_collection import (
    WeightCollectionCreate,
    WeightCollectionUpdate,
    WeightCollectionResponse,
    WeightCollectionListResponse,
    WeightDashboardResponse,
)
from app.services.t_weight_collection import (
    create_weight_collection,
    update_weight_collection,
    get_weight_by_tag_id,
    get_weight_by_animal_id,
    get_weight_by_category_id,
    delete_weight_by_tag_id,
    get_all_weight_records,
    get_weight_dashboard,
)
from app.api.auth import get_current_active_user

router = APIRouter(prefix="/api/v1/track/weight", tags=["weight_collection"])


@router.post("/create", response_model=dict)
async def create_weight_collection_endpoint(
    payload: WeightCollectionCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """Create a new weight record for an animal identified by tag_id."""
    record = await create_weight_collection(db, payload.dict(), current_user)
    return {"message": "Weight record created successfully", "record_id": record.id}


@router.patch("/update/{record_id}", response_model=dict)
async def update_weight_collection_endpoint(
    record_id: int,
    payload: WeightCollectionUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """Update an existing weight record by its ID."""
    try:
        record = await update_weight_collection(
            db, record_id, payload.dict(exclude_unset=True), current_user
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return record


@router.get("/list", response_model=WeightCollectionListResponse)
async def list_all_weight_records_endpoint(
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """List all weight records for the current user with pagination.

    - **offset**: number of records to skip (default 0)
    - **limit**: maximum records to return (default 50)
    """
    records, count = await get_all_weight_records(db, current_user, offset, limit)

    return WeightCollectionListResponse(
        count=count,
        records=[
            WeightCollectionResponse(
                id=r.id,
                animal_id=r.animal_id,
                animal_tag_id=getattr(r, "animal_tag_id", None),
                category_name=getattr(r, "category_name", None),
                category_species=getattr(r, "category_species", None),
                weight_kg=r.weight_kg,
                weight_date=r.weight_date,
                weight_unit=r.weight_unit,
                notes=r.notes,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in records
        ],
    )


@router.get("/tag/{tag_id}", response_model=WeightCollectionListResponse)
async def get_weight_by_tag_id_endpoint(
    tag_id: str,
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """Get weight records by animal tag ID (partial match)."""
    try:
        records, count = await get_weight_by_tag_id(
            db, tag_id, current_user, offset, limit
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return WeightCollectionListResponse(
        count=count,
        records=[
            WeightCollectionResponse(
                id=r.id,
                animal_id=r.animal_id,
                animal_tag_id=getattr(r, "animal_tag_id", None),
                category_name=getattr(r, "category_name", None),
                category_species=getattr(r, "category_species", None),
                weight_kg=r.weight_kg,
                weight_date=r.weight_date,
                weight_unit=r.weight_unit,
                notes=r.notes,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in records
        ],
    )


@router.get("/animal/{animal_id}", response_model=WeightCollectionListResponse)
async def get_weight_by_animal_id_endpoint(
    animal_id: int,
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """Get weight records by animal tracking ID."""
    try:
        records, count = await get_weight_by_animal_id(
            db, animal_id, current_user, offset, limit
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return WeightCollectionListResponse(
        count=count,
        records=[
            WeightCollectionResponse(
                id=r.id,
                animal_id=r.animal_id,
                animal_tag_id=getattr(r, "animal_tag_id", None),
                category_name=getattr(r, "category_name", None),
                category_species=getattr(r, "category_species", None),
                weight_kg=r.weight_kg,
                weight_date=r.weight_date,
                weight_unit=r.weight_unit,
                notes=r.notes,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in records
        ],
    )


@router.get("/category/{category_id}", response_model=WeightCollectionListResponse)
async def get_weight_by_category_id_endpoint(
    category_id: int,
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """Get weight records for all animals belonging to a category (Animal) ID."""
    try:
        records, count = await get_weight_by_category_id(
            db, category_id, current_user, offset, limit
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return WeightCollectionListResponse(
        count=count,
        records=[
            WeightCollectionResponse(
                id=r.id,
                animal_id=r.animal_id,
                animal_tag_id=getattr(r, "animal_tag_id", None),
                category_name=getattr(r, "category_name", None),
                category_species=getattr(r, "category_species", None),
                weight_kg=r.weight_kg,
                weight_date=r.weight_date,
                weight_unit=r.weight_unit,
                notes=r.notes,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in records
        ],
    )


@router.delete("/delete/{tag_id}", response_model=dict)
async def delete_weight_by_tag_id_endpoint(
    tag_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """Delete ALL weight records for an animal identified by exact tag_id."""
    try:
        deleted_count = await delete_weight_by_tag_id(db, tag_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "message": f"Deleted {deleted_count} weight record(s) for tag_id '{tag_id}'"
    }


@router.get("/dashboard", response_model=WeightDashboardResponse)
async def get_weight_dashboard_endpoint(
    months: int = 12,
    growth_threshold_kg_per_month: float = 2.0,
    animal_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """
    Return dashboard analytics for the weight-collection section.

    - **months**: lookback window for trend and monthly charts (default 12)
    - **growth_threshold_kg_per_month**: animals growing below this value will
      appear in the low-growth alert table (default 2.0 kg/month)
    - **animal_id**: optional Tracking_Animal.id – when provided, all dashboard
      data is scoped to that single animal
    """
    data = await get_weight_dashboard(
        db,
        current_user,
        months=months,
        growth_threshold_kg_per_month=growth_threshold_kg_per_month,
        animal_id=animal_id,
    )
    return WeightDashboardResponse(
        kpi=data["kpi"],
        growth_trend=data["growth_trend"],
        monthly_avg=data["monthly_avg"],
        top_heaviest=data["top_heaviest"],
        weight_distribution=data["weight_distribution"],
    )
