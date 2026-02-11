from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from app.models.tables import Order, OrderItem, Animal, Tracking_Animal
from app.schemas.users import User


async def dashboard_stats(main_db: AsyncSession, current_user: User) -> dict:
    # 1. Total Animals
    # Use .scalar() to get the single integer directly
    result = await main_db.execute(select(func.count(Animal.id)).filter(Animal.created_by == str(current_user.unique_id)))
    total_animals = result.scalar() or 0

    # 2. Tracking Animals Status Count
    status_counts_result = await main_db.execute(
        select(
            Tracking_Animal.status, func.count(Tracking_Animal.id).label("count")
        ).group_by(Tracking_Animal.status).filter(Tracking_Animal.created_by == str(current_user.unique_id))
    )
    # Using a dict comprehension on the results
    tracking_animal_status_counts = {
        row.status: row.count for row in status_counts_result
    }

    # 3. Order Status Stats
    order_stats_query = await main_db.execute(
        select(
            Order.order_status.label("status"),
            func.count(Order.id).label("count"),
            func.sum(Order.total).label("total_amount"),
            func.coalesce(func.sum(OrderItem.quantity), 0).label("total_quantity"),
        )
        .outerjoin(OrderItem, Order.id == OrderItem.order_id)
        .group_by(Order.order_status)
        .filter(Order.created_by == str(current_user.unique_id))
    )

    # Using .mappings() allows you to treat rows like dictionaries
    order_status_counts = []
    for row in order_stats_query.mappings():
        order_status_counts.append(
            {
                "status": row["status"],
                "count": row["count"],
                "total_amount": float(row["total_amount"])
                if row["total_amount"]
                else 0.0,
                "total_quantity": int(row["total_quantity"]),
            }
        )

    return {
        "total_animal_types": total_animals,
        "tracking_animal_status_counts": tracking_animal_status_counts,
        "order_status_counts": order_status_counts,
    }
