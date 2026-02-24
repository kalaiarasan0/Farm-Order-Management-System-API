from sqlalchemy import select, func
from typing import List, Optional, Any
from datetime import date
from app.db.database import AsyncSessionLocal
from app.models.tables import Tracking_Animal, AnimalEvent, MilkCollection
from app.graphql.types import (
    MilkProductionAnalytics,
    EventDistribution,
    HerdStats,
    BirthVsPurchaseAnalytics,
    GenderDistribution,
)


async def get_milk_analytics(
    start_date: date,
    end_date: date,
    animal_id: Optional[int] = None,
    period: str = "DAY",  # DAY, WEEK, MONTH, YEAR
) -> List[MilkProductionAnalytics]:
    async with AsyncSessionLocal() as db:
        # Determine grouping
        if period == "YEAR":
            time_format = "%Y"
            group_expr = func.date_format(MilkCollection.collection_date, time_format)
        elif period == "MONTH":
            time_format = "%Y-%m"
            group_expr = func.date_format(MilkCollection.collection_date, time_format)
        elif period == "WEEK":
            time_format = "%x-W%v"  # ISO week
            group_expr = func.date_format(MilkCollection.collection_date, time_format)
        else:  # DAY
            group_expr = MilkCollection.collection_date

        query = (
            select(
                group_expr.label("period"),
                func.min(MilkCollection.collection_date).label(
                    "date"
                ),  # Representative date
                func.sum(MilkCollection.quantity).label("total_milk"),
                func.avg(MilkCollection.milk_fat).label("avg_fat"),
                func.avg(MilkCollection.milk_snf).label("avg_snf"),
            )
            .where(
                MilkCollection.collection_date >= start_date,
                MilkCollection.collection_date <= end_date,
            )
            .group_by(group_expr)
            .order_by(func.min(MilkCollection.collection_date))
        )

        if animal_id:
            query = query.where(MilkCollection.animal_id == animal_id)

        result = await db.execute(query)
        rows = result.all()

        return [
            MilkProductionAnalytics(
                period=str(row.period),
                date=row.date
                if period == "DAY"
                else row.date,  # Return first date of period as reference
                total_milk=float(row.total_milk or 0),
                avg_fat=float(row.avg_fat or 0),
                avg_snf=float(row.avg_snf or 0),
            )
            for row in rows
        ]


async def get_event_distribution(
    start_date: date, end_date: date
) -> List[EventDistribution]:
    async with AsyncSessionLocal() as db:
        query = (
            select(AnimalEvent.event_type, func.count(AnimalEvent.id).label("count"))
            .where(
                AnimalEvent.event_date >= start_date, AnimalEvent.event_date <= end_date
            )
            .group_by(AnimalEvent.event_type)
        )

        result = await db.execute(query)
        rows = result.all()

        return [
            EventDistribution(event_type=str(row.event_type), count=row.count)
            for row in rows
        ]


def get_enum_value(enum_val: Any) -> str:
    if hasattr(enum_val, "value"):
        return str(enum_val.value)
    return str(enum_val)


async def get_herd_stats() -> List[HerdStats]:
    async with AsyncSessionLocal() as db:
        query = select(
            Tracking_Animal.status, func.count(Tracking_Animal.id).label("count")
        ).group_by(Tracking_Animal.status)

        result = await db.execute(query)
        rows = result.all()

        return [
            HerdStats(status=get_enum_value(row.status), count=row.count)
            for row in rows
        ]


async def get_birth_vs_purchase(
    start_date: date,
    end_date: date,
    period: str = "MONTH",  # MONTH or YEAR
) -> List[BirthVsPurchaseAnalytics]:
    async with AsyncSessionLocal() as db:
        # Using func.date_format for MySQL: %Y-%m
        time_format = "%Y-%m" if period == "MONTH" else "%Y"

        # Helper to run query for birth and purchase
        async def fetch_counts(date_col):
            stmt = (
                select(
                    func.date_format(date_col, time_format).label("period"),
                    func.count(Tracking_Animal.id).label("count"),
                )
                .where(date_col >= start_date, date_col <= end_date)
                .group_by(func.date_format(date_col, time_format))
            )
            return (await db.execute(stmt)).all()

        birth_rows = await fetch_counts(Tracking_Animal.birth_date)
        purchase_rows = await fetch_counts(Tracking_Animal.purchase_date)

        birth_data = {row.period: row.count for row in birth_rows}
        purchase_data = {row.period: row.count for row in purchase_rows}

        all_periods = sorted(set(birth_data.keys()) | set(purchase_data.keys()))

        return [
            BirthVsPurchaseAnalytics(
                period=p,
                birth_count=birth_data.get(p, 0),
                purchase_count=purchase_data.get(p, 0),
            )
            for p in all_periods
        ]


async def get_gender_distribution() -> List[GenderDistribution]:
    async with AsyncSessionLocal() as db:
        query = select(
            Tracking_Animal.gender, func.count(Tracking_Animal.id).label("count")
        ).group_by(Tracking_Animal.gender)

        result = await db.execute(query)
        rows = result.all()

        return [
            GenderDistribution(gender=str(row.gender), count=row.count) for row in rows
        ]
