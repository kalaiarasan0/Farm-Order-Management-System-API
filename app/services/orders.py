from decimal import Decimal
from typing import List, Optional, Dict
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import uuid
from app.models.tables import (
    Inventory,
    Order,
    OrderItem,
    Customer,
    Animal,
    Tracking_Animal,
)
from app.schemas.enums import OrderStatus
from sqlalchemy import update
from app.schemas.users import User
from sqlalchemy.exc import IntegrityError


async def create_order(
    db: AsyncSession,
    *,
    current_user: User,  # Added current_user
    customer_id: int | None = None,
    customer_data: Optional[Dict] = None,
    items: List[dict],
    shipping: float = 0.0,
    tax: float = 0.0,
    billing_address_id: int | None = None,
    shipping_address_id: int | None = None,
) -> Order:
    """
    Create an order with items. This simple implementation:
    - validates inventory quantity is available
    - decrements inventory
    - creates Order and OrderItems
    Note: caller should pass a DB session coming from `get_db()` dependency.
    """
    # compute subtotal and validate stock
    subtotal = Decimal("0.00")

    # require customer information
    if not customer_id and not customer_data:
        raise HTTPException(
            status_code=400,
            detail="customer_id or customer_data is required to create an order",
        )

    # perform within transaction
    async with db.begin():
        # If caller provided customer data (instead of id), create the customer inside this transaction
        if not customer_id and customer_data:
            cust = Customer(
                first_name=customer_data.get("first_name"),
                last_name=customer_data.get("last_name"),
                email=customer_data.get("email"),
                phone=customer_data.get("phone"),
            )
            db.add(cust)
            await db.flush()
            customer_id = cust.id

        check_customer = await db.get(Customer, customer_id)
        if not check_customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Lock and validate inventory rows (simple approach)
        inventory_map = {}
        for it in items:
            inv = None
            if it.get("inventory_id"):
                inv = await db.get(Inventory, it["inventory_id"])  # type: ignore[arg-type]
            else:
                # try to find an inventory entry for the animal
                result = await db.execute(
                    select(Inventory)
                    .where(Inventory.animal_id == it["category_id"])
                    .limit(1)
                )
                inv = result.scalars().first()

            if not inv:
                raise HTTPException(
                    status_code=404,
                    detail=f"Inventory not found for animal_id={it['category_id']}",
                )

            if inv.quantity < it["quantity"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for inventory id {inv.id}",
                )

            inventory_map[it.get("inventory_id") or inv.id] = inv

            # Resolve unit price: prefer input override, else DB price
            unit_price = Decimal(str(it.get("unit_price", 0.0)))
            if unit_price <= 0:
                unit_price = (
                    inv.unit_price if inv.unit_price is not None else Decimal("0.00")
                )
            quantity = Decimal(it["quantity"])
            gross_price = quantity * unit_price

            discount_val = Decimal(str(it.get("discount_value", 0.0)))
            discount_pct = Decimal(str(it.get("discount_percent", 0.0)))

            if discount_val > 0:
                pass
            elif discount_pct > 0:
                discount_val = gross_price * (discount_pct / Decimal("100.0"))

            if discount_val > gross_price:
                discount_val = gross_price

            line_total = gross_price - discount_val
            subtotal += line_total

        # create order
        order = Order(
            order_number=_generate_order_number(db),
            customer_id=customer_id or 0,
            billing_address_id=billing_address_id or None,
            shipping_address_id=shipping_address_id or None,
            order_status=OrderStatus.PENDING,
            subtotal=subtotal,
            shipping=Decimal(str(shipping)),
            tax=Decimal(str(tax)),
            total=subtotal + Decimal(str(shipping)) + Decimal(str(tax)),
            created_by=str(current_user.unique_id),
        )
        db.add(order)
        await db.flush()  # populate order.id

        # create order items and decrement inventory
        for it in items:
            inv_id = it.get("inventory_id") or next(
                k for k, v in inventory_map.items() if v.animal_id == it["category_id"]
            )
            inv = inventory_map[inv_id]

            # Resolve unit price: prefer input override, else DB price
            unit_price = Decimal(str(it.get("unit_price", 0.0)))
            if unit_price <= 0:
                unit_price = (
                    inv.unit_price if inv.unit_price is not None else Decimal("0.00")
                )
            quantity = Decimal(it["quantity"])
            gross_price = quantity * unit_price

            # Discount logic
            discount_val = Decimal(str(it.get("discount_value", 0.0)))
            discount_pct = Decimal(str(it.get("discount_percent", 0.0)))

            if discount_val > 0:
                # Value takes precedence or is the source
                # distinct_pct = (discount_val / gross_price) * 100 if gross_price else 0
                pass
            elif discount_pct > 0:
                discount_val = gross_price * (discount_pct / Decimal("100.0"))

            # Ensure discount doesn't exceed gross price
            if discount_val > gross_price:
                discount_val = gross_price

            total_price = gross_price - discount_val

            order_item = OrderItem(
                order_id=order.id,
                animal_id=it["category_id"],
                inventory_id=inv.id,
                quantity=it["quantity"],
                unit_price=unit_price,
                gross_price=gross_price,
                discount_value=discount_val,
                discount_percent=discount_pct,
                total_price=total_price,
                created_by=str(current_user.unique_id),
            )
            db.add(order_item)

            # decrement inventory
            inv.quantity = inv.quantity - it["quantity"]
            db.add(inv)

        await db.flush()

    # refresh and return
    # refresh and return with loaded relationships
    # We need explicit refresh of items because they were just added in this transaction
    # And we also need nested animal for the response if the API uses it immediately
    await db.refresh(order, ["items"])

    # However, db.refresh taking list of attribute names only works for immediate attributes.
    # To load nested `items.animal`, we might need a separate query or ensure they are loaded.
    # Since `items` are loaded, accessing `item.animal` will trigger lazy load (fails in async).
    # We should iterate and ensure they are loaded or use a select strategy.

    # A cleaner pattern in async is to execute a select with options to reload the object.
    # Or iterate and await a refresh on items if needed? No, that's N+1.

    # Let's reload the order completely with necessary options.
    statement = (
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.animal))
        .where(Order.id == order.id)
    )
    result = await db.execute(statement)
    order = result.scalars().first()

    return order


async def get_order_by_id(db: AsyncSession, order_id: int, current_user: User) -> Order | None:
    """Return an Order by id, or None if not found."""
    result = await db.execute(
        select(Order)
        .filter(Order.id == order_id, Order.created_by == str(current_user.unique_id))
        .options(
            selectinload(Order.items).selectinload(OrderItem.tracking_animals),
            selectinload(Order.items).selectinload(OrderItem.animal),
            selectinload(Order.customer),
        )
    )
    return result.scalars().first()


async def list_orders(db: AsyncSession, current_user: User, limit: int = 50, offset: int = 0):
    """Return a list of orders with pagination."""
    result = (
        select(Order)
        .filter(Order.created_by == str(current_user.unique_id))
        .options(
            selectinload(Order.items).selectinload(OrderItem.animal),
            selectinload(Order.customer),
        )
        .order_by(Order.id.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(result)
    order_list = result.scalars().all()

    # print(order_list)

    count_result = await db.execute(select(func.count(Order.id)).filter(Order.created_by == str(current_user.unique_id)))
    order_count = count_result.scalar_one()

    return order_list, order_count


async def search_orders(
    db: AsyncSession, query_str: str, current_user: User, limit: int = 50, offset: int = 0
):
    """Search orders by order number, customer name, or category (animal) name."""
    from sqlalchemy import or_

    # We need to distinct() because joining OrderItems/Animals might multiply rows
    query = (
        select(Order)
        .join(Customer)
        .outerjoin(OrderItem, Order.items)  # Join OrderItems to link to Animal
        .outerjoin(Animal, OrderItem.animal)  # Join Animal
        .filter(Order.created_by == str(current_user.unique_id),
            or_(
                Order.order_number.ilike(f"%{query_str}%"),
                Customer.first_name.ilike(f"%{query_str}%"),
                Customer.last_name.ilike(f"%{query_str}%"),
                Animal.name.ilike(f"%{query_str}%"),
            )
        )
        .distinct()
        .options(
            selectinload(Order.items).selectinload(OrderItem.animal),
            selectinload(Order.customer),
        )
    )

    result = await db.execute(
        query.order_by(Order.id.desc()).limit(limit).offset(offset)
    )
    orders = result.scalars().all()

    # Check if there is an easy way to get count from distinct query in async without subquery overhead
    # For now, just re-execute with count or use separate count
    # Actually, simplest is to use func.count on the same query

    # Re-building query for count manually as sqlalchemy async count on distinct can be tricky
    count_stmt = select(func.count(Order.id)).select_from(query.subquery())
    # Wait, query is a SELECT statement, subquery() makes it a selectable

    count_result = await db.execute(count_stmt)
    count = count_result.scalar_one()

    return orders, count


def _generate_order_number(db: AsyncSession) -> str:
    # Use a UUID4-based short order number to avoid race conditions
    return f"ORD-{uuid.uuid4().hex[:12].upper()}"


async def update_order_status(
    db: AsyncSession, order_id: int, status: OrderStatus, current_user: User
):
    if status not in OrderStatus:
        raise HTTPException(status_code=400, detail="Invalid order status")

    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.order_status == status:
        raise HTTPException(status_code=400, detail="Order status is already set")

    # Validate mapping for all items
    # Need to load items
    # Or fetch them
    # order.items might not be loaded if we just used db.get which doesn't default eager load everything unless configured
    # Let's ensure items are loaded

    # We can reload order with items
    # Validate mapping for all items
    # Ensure items are loaded
    if "items" not in order.__dict__:
        # Reload order with items
        stmt = (
            select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
        )
        result = await db.execute(stmt)
        order = result.scalars().first()

    for item in order.items:
        # Need to fix lazy load of animal
        # Just use item.animal but ensure it's loaded?
        # Actually checking count of TrackingAnimal
        result = await db.execute(
            select(func.count(Tracking_Animal.id)).filter(
                Tracking_Animal.order_item_id == item.id
            )
        )
        mapped_count = result.scalar_one()

        if mapped_count != item.quantity:
            # Need item.animal.name, fetch it if needed
            # For robustness, fetch item with animal name
            stmt_item = (
                select(OrderItem)
                .options(selectinload(OrderItem.animal))
                .where(OrderItem.id == item.id)
            )
            res_item = await db.execute(stmt_item)
            item_loaded = res_item.scalar_one()

            raise HTTPException(
                status_code=400,
                detail=f"Order Number {order.order_number} (category : {item_loaded.animal.name}) generally requires {item.quantity} quantity, but only {mapped_count} are mapped.",
            )

    try:
        # Update Order Status
        order.order_status = status
        order.updated_by = str(current_user.unique_id)
        db.add(order)

        # Update Tracking Animals Status
        # We can do a bulk update for efficiency
        item_ids = [item.id for item in order.items]
        if item_ids:
            stmt = (
                update(Tracking_Animal)
                .where(Tracking_Animal.order_item_id.in_(item_ids))
                .values(order_status=status)
            )
            await db.execute(stmt)

        await db.commit()
        await db.refresh(order)
        return {"message": "Order status updated successfully"}
    except Exception as e:
        await db.rollback()
        raise ValueError(str(e))


async def update_order_items_status(
    db: AsyncSession,
    order_id: int,
    item_ids: List[int],
    status: OrderStatus,
    current_user: User,
) -> dict:
    # Check if order exists
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Validate all items belong to this order
    stmt_check = select(OrderItem.id).where(
        OrderItem.id.in_(item_ids), OrderItem.order_id == order_id
    )
    result_check = await db.execute(stmt_check)
    found_ids = result_check.scalars().all()

    if len(set(found_ids)) != len(set(item_ids)):
        found_set = set(found_ids)
        missing = [iid for iid in item_ids if iid not in found_set]
        raise HTTPException(
            status_code=400,
            detail=f"Order items {missing} do not belong to order {order_id}",
        )

    try:
        # Update Tracking Animals Status
        stmt = (
            update(Tracking_Animal)
            .where(Tracking_Animal.order_item_id.in_(item_ids))
            .values(order_status=status, updated_by=str(current_user.unique_id))
        )
        await db.execute(stmt)
        await db.commit()

        return {"message": "Order items updated successfully"}

    except Exception as e:
        await db.rollback()
        raise ValueError(str(e))

async def delete_order(db: AsyncSession, order_id: int, current_user: User) -> dict:
    try:
        order = await db.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        await db.delete(order)
        await db.commit()
        return {"message": "Order deleted successfully"}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Order is associated with an animal")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


async def delete_order_item(db: AsyncSession, order_item_id: int, current_user: User) -> dict:
    try:
        order_item = await db.get(OrderItem, order_item_id)
        if not order_item:
            raise HTTPException(status_code=404, detail="Order item not found")

        await db.delete(order_item)
        await db.commit()
        return {"message": "Order item deleted successfully"}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Order item is associated with an animal")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))



# async def main():
#     from app.db.database import AsyncSessionLocal

#     async with AsyncSessionLocal() as db_main:
#         try:
#             orders, orders_count = await list_orders(db_main)
#             # for e in events:
#             #     print(vars(e))
#             print("Synced events:", orders_count)
#             print("Synced events:", orders)
#         except Exception as e:
#             print(f"Error: {e}")


# if __name__ == "__main__":
#     import asyncio

#     asyncio.run(main())
