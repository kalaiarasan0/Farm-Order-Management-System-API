from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.exc import SQLAlchemyError
from app.models.tables import Animal as Main_Animal, Tracking_Animal, WeightCollection
from fastapi import HTTPException
from sqlalchemy import select, func
from app.schemas.users import User
from datetime import date


def _attach_animal_info(records: list, main_animal_map: dict) -> None:
    """Attach category_name, category_species, and animal_tag_id to each record."""
    for rec in records:
        if rec.animal:
            rec.animal_tag_id = rec.animal.tag_id
            if rec.animal.category_id in main_animal_map:
                ma = main_animal_map[rec.animal.category_id]
                rec.category_name = ma.name
                rec.category_species = ma.species


async def _fetch_main_animal_map(db: AsyncSession, category_ids: set) -> dict:
    if not category_ids:
        return {}
    result = await db.execute(
        select(Main_Animal).filter(Main_Animal.id.in_(category_ids))
    )
    main_animals = result.scalars().all()
    return {ma.id: ma for ma in main_animals}


async def create_weight_collection(
    db: AsyncSession, data: dict, current_user: User
) -> WeightCollection:
    """Create a weight record. Resolves animal_tag_id → animal_id."""
    tag_id: str = data.get("animal_tag_id", "")

    tracking_animal = (
        await db.execute(
            select(Tracking_Animal).filter(
                Tracking_Animal.tag_id == tag_id,
                Tracking_Animal.created_by == str(current_user.unique_id),
            )
        )
    ).scalar_one_or_none()

    if tracking_animal is None:
        raise HTTPException(status_code=404, detail=f"Animal '{tag_id}' not found")

    try:
        record = WeightCollection(
            animal_id=tracking_animal.id,
            weight_date=data.get("weight_date"),
            weight_kg=data["weight_kg"],
            weight_unit=data.get("weight_unit", "kg"),
            notes=data.get("notes"),
            created_by=str(current_user.unique_id),
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record
    except SQLAlchemyError:
        await db.rollback()
        raise


async def update_weight_collection(
    db: AsyncSession, record_id: int, data: dict, current_user: User
) -> WeightCollection:
    """Update a weight record by its primary key."""
    record = (
        await db.execute(
            select(WeightCollection).filter(
                WeightCollection.id == record_id,
                WeightCollection.created_by == str(current_user.unique_id),
            )
        )
    ).scalar_one_or_none()

    if record is None:
        raise HTTPException(status_code=404, detail="Weight record not found")

    for field, value in data.items():
        if value is not None and hasattr(record, field):
            setattr(record, field, value)

    record.updated_by = str(current_user.unique_id)

    try:
        await db.commit()
        await db.refresh(record)
        return dict(message="Weight record updated successfully", record_id=record.id)
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Weight record not updated")


async def get_weight_by_tag_id(
    db: AsyncSession,
    tag_id: str,
    current_user: User,
    offset: int = 0,
    limit: int = 50,
) -> Tuple[List[WeightCollection], int]:
    """Return weight records for animals whose tag_id matches (partial)."""
    pattern = f"%{tag_id}%"

    # First resolve matching Tracking_Animal ids
    tracking_result = await db.execute(
        select(Tracking_Animal.id).filter(
            Tracking_Animal.tag_id.ilike(pattern),
            Tracking_Animal.created_by == str(current_user.unique_id),
        )
    )
    animal_ids = [row[0] for row in tracking_result.all()]

    if not animal_ids:
        return [], 0

    query = (
        select(WeightCollection)
        .filter(WeightCollection.animal_id.in_(animal_ids))
        .options(selectinload(WeightCollection.animal))
        .offset(offset)
        .limit(limit)
    )
    records = (await db.execute(query)).scalars().all()

    count = (
        await db.execute(
            select(func.count(WeightCollection.id)).filter(
                WeightCollection.animal_id.in_(animal_ids)
            )
        )
    ).scalar_one()

    category_ids = {r.animal.category_id for r in records if r.animal}
    main_animal_map = await _fetch_main_animal_map(db, category_ids)
    _attach_animal_info(records, main_animal_map)

    return records, count


async def get_weight_by_animal_id(
    db: AsyncSession,
    animal_id: int,
    current_user: User,
    offset: int = 0,
    limit: int = 50,
) -> Tuple[List[WeightCollection], int]:
    """Return weight records for a specific tracking animal ID."""
    query = (
        select(WeightCollection)
        .filter(
            WeightCollection.animal_id == animal_id,
            WeightCollection.created_by == str(current_user.unique_id),
        )
        .options(selectinload(WeightCollection.animal))
        .offset(offset)
        .limit(limit)
    )
    records = (await db.execute(query)).scalars().all()

    count = (
        await db.execute(
            select(func.count(WeightCollection.id)).filter(
                WeightCollection.animal_id == animal_id,
                WeightCollection.created_by == str(current_user.unique_id),
            )
        )
    ).scalar_one()

    category_ids = {r.animal.category_id for r in records if r.animal}
    main_animal_map = await _fetch_main_animal_map(db, category_ids)
    _attach_animal_info(records, main_animal_map)

    return records, count


async def get_weight_by_category_id(
    db: AsyncSession,
    category_id: int,
    current_user: User,
    offset: int = 0,
    limit: int = 50,
) -> Tuple[List[WeightCollection], int]:
    """Return weight records for all animals belonging to a category."""
    # Resolve tracking animal ids for this category
    tracking_result = await db.execute(
        select(Tracking_Animal.id).filter(
            Tracking_Animal.category_id == category_id,
            Tracking_Animal.created_by == str(current_user.unique_id),
        )
    )
    animal_ids = [row[0] for row in tracking_result.all()]

    if not animal_ids:
        return [], 0

    query = (
        select(WeightCollection)
        .filter(WeightCollection.animal_id.in_(animal_ids))
        .options(selectinload(WeightCollection.animal))
        .offset(offset)
        .limit(limit)
    )
    records = (await db.execute(query)).scalars().all()

    count = (
        await db.execute(
            select(func.count(WeightCollection.id)).filter(
                WeightCollection.animal_id.in_(animal_ids)
            )
        )
    ).scalar_one()

    # All share the same category_id, so map is simple
    main_animal_map = await _fetch_main_animal_map(db, {category_id})
    _attach_animal_info(records, main_animal_map)

    return records, count


async def get_all_weight_records(
    db: AsyncSession,
    current_user: User,
    offset: int = 0,
    limit: int = 50,
) -> Tuple[List[WeightCollection], int]:
    """Return all weight records belonging to the current user, with pagination."""
    query = (
        select(WeightCollection)
        .filter(WeightCollection.created_by == str(current_user.unique_id))
        .options(selectinload(WeightCollection.animal))
        .order_by(WeightCollection.weight_date.desc())
        .offset(offset)
        .limit(limit)
    )
    records = (await db.execute(query)).scalars().all()

    count = (
        await db.execute(
            select(func.count(WeightCollection.id)).filter(
                WeightCollection.created_by == str(current_user.unique_id)
            )
        )
    ).scalar_one()

    category_ids = {r.animal.category_id for r in records if r.animal}
    main_animal_map = await _fetch_main_animal_map(db, category_ids)
    _attach_animal_info(records, main_animal_map)

    return records, count


async def delete_weight_by_tag_id(
    db: AsyncSession, tag_id: str, current_user: User
) -> int:
    """Delete ALL weight records for the animal with the given exact tag_id.
    Returns the number of records deleted."""
    tracking_animal = (
        await db.execute(
            select(Tracking_Animal).filter(
                Tracking_Animal.tag_id == tag_id,
                Tracking_Animal.created_by == str(current_user.unique_id),
            )
        )
    ).scalar_one_or_none()

    if tracking_animal is None:
        raise HTTPException(
            status_code=404, detail=f"Tracking animal with tag_id '{tag_id}' not found"
        )

    records = (
        (
            await db.execute(
                select(WeightCollection).filter(
                    WeightCollection.animal_id == tracking_animal.id,
                    WeightCollection.created_by == str(current_user.unique_id),
                )
            )
        )
        .scalars()
        .all()
    )

    count = len(records)
    for rec in records:
        await db.delete(rec)

    try:
        await db.commit()
        return count
    except SQLAlchemyError:
        await db.rollback()
        raise


# ── Dashboard ─────────────────────────────────────────────────────────────────


async def get_weight_dashboard(
    db: AsyncSession,
    current_user: User,
    months: int = 12,
    growth_threshold_kg_per_month: float = 2.0,
    animal_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Return all data required for the weight-collection dashboard in one call.

    If ``animal_id`` (Tracking_Animal.id) is provided, every section is
    scoped to that single animal.  Otherwise the dashboard covers all
    animals owned by the current user.

    Sections
    --------
    kpi                : total_animals, avg_weight, max_weight
    growth_trend       : per-animal (tag_id, date, weight_kg) for the last `months`
    monthly_avg        : farm-wide avg weight per calendar month (last `months`)
    top_heaviest       : top-10 animals by MAX(weight_kg)
    weight_distribution: 10-bin histogram over all weight_kg values
    """
    user_id = str(current_user.unique_id)
    cutoff_date = date.today().replace(day=1)
    # Compute cutoff N months back
    year = cutoff_date.year
    month = cutoff_date.month - months
    while month <= 0:
        month += 12
        year -= 1
    trend_start = date(year, month, 1)

    # ── Build a common filter list used by every section ──────────────────────
    base_filters = [WeightCollection.created_by == user_id]
    if animal_id is not None:
        base_filters.append(WeightCollection.animal_id == animal_id)

    # ── 1. KPI Stats ──────────────────────────────────────────────────────────
    kpi_result = await db.execute(
        select(
            func.count(func.distinct(WeightCollection.animal_id)).label(
                "total_animals"
            ),
            func.avg(WeightCollection.weight_kg).label("avg_weight"),
            func.max(WeightCollection.weight_kg).label("max_weight"),
        ).where(*base_filters)
    )
    kpi_row = kpi_result.one()
    kpi = {
        "total_animals": int(kpi_row.total_animals or 0),
        "avg_weight": round(float(kpi_row.avg_weight or 0), 2),
        "max_weight": round(float(kpi_row.max_weight or 0), 2),
    }

    # ── 2. Growth Trend (per animal, ordered by date) ─────────────────────────
    trend_rows = (
        await db.execute(
            select(
                Tracking_Animal.tag_id,
                WeightCollection.weight_date,
                WeightCollection.weight_kg,
            )
            .join(Tracking_Animal, WeightCollection.animal_id == Tracking_Animal.id)
            .where(
                *base_filters,
                WeightCollection.weight_date >= trend_start,
            )
            .order_by(Tracking_Animal.tag_id, WeightCollection.weight_date)
        )
    ).all()

    growth_trend = [
        {"tag_id": r.tag_id, "date": r.weight_date, "weight_kg": r.weight_kg}
        for r in trend_rows
        if r.weight_date is not None
    ]

    # ── 3. Monthly Farm Avg Weight ────────────────────────────────────────────
    monthly_rows = (
        await db.execute(
            select(
                func.date_format(WeightCollection.weight_date, "%Y-%m").label("month"),
                func.avg(WeightCollection.weight_kg).label("avg_weight"),
            )
            .where(
                *base_filters,
                WeightCollection.weight_date >= trend_start,
            )
            .group_by(func.date_format(WeightCollection.weight_date, "%Y-%m"))
            .order_by(func.date_format(WeightCollection.weight_date, "%Y-%m"))
        )
    ).all()

    monthly_avg = [
        {"month": r.month, "avg_weight": round(float(r.avg_weight or 0), 2)}
        for r in monthly_rows
        if r.month
    ]

    # ── 4. Top 10 Heaviest Animals ────────────────────────────────────────────
    top_rows = (
        await db.execute(
            select(
                Tracking_Animal.tag_id,
                Main_Animal.name.label("category_name"),
                func.max(WeightCollection.weight_kg).label("max_weight"),
            )
            .join(Tracking_Animal, WeightCollection.animal_id == Tracking_Animal.id)
            .join(
                Main_Animal,
                Tracking_Animal.category_id == Main_Animal.id,
                isouter=True,
            )
            .where(*base_filters)
            .group_by(
                WeightCollection.animal_id,
                Tracking_Animal.tag_id,
                Main_Animal.name,
            )
            .order_by(func.max(WeightCollection.weight_kg).desc())
            .limit(10)
        )
    ).all()

    top_heaviest = [
        {
            "tag_id": r.tag_id,
            "category_name": r.category_name,
            "max_weight": round(float(r.max_weight or 0), 2),
        }
        for r in top_rows
    ]

    # ── 5. Weight Distribution (10 equal-width bins) ──────────────────────────
    all_weights_rows = (
        (await db.execute(select(WeightCollection.weight_kg).where(*base_filters)))
        .scalars()
        .all()
    )

    weight_distribution: List[Dict[str, Any]] = []
    if all_weights_rows:
        w_min = min(all_weights_rows)
        w_max = max(all_weights_rows)
        if w_min == w_max:
            weight_distribution = [
                {"bucket_label": f"{w_min:.0f} kg", "count": len(all_weights_rows)}
            ]
        else:
            num_bins = 10
            bin_width = (w_max - w_min) / num_bins
            bins = [0] * num_bins
            for w in all_weights_rows:
                idx = min(int((w - w_min) / bin_width), num_bins - 1)
                bins[idx] += 1
            for i in range(num_bins):
                lo = w_min + i * bin_width
                hi = lo + bin_width
                weight_distribution.append(
                    {
                        "bucket_label": f"{lo:.0f}–{hi:.0f} kg",
                        "count": bins[i],
                    }
                )

    return {
        "kpi": kpi,
        "growth_trend": growth_trend,
        "monthly_avg": monthly_avg,
        "top_heaviest": top_heaviest,
        "weight_distribution": weight_distribution,
    }
