from decimal import Decimal
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy import select, update
import uuid

from app.models.tables import (
    Inventory,
    Order,
    OrderItem,
    Customer,
)


def get_order_by_id(db: Session, order_id: int) -> Order | None:
    """Return an Order by id, or None if not found."""
    return db.query(Order).filter(Order.id == order_id).options().first()


def list_orders(db: Session, limit: int = 50, offset: int = 0):
    """Return a list of orders with pagination."""
    return db.query(Order).order_by(Order.id.desc()).limit(limit).offset(offset).all()


def _generate_order_number(db: Session) -> str:
    # Use a UUID4-based short order number to avoid race conditions
    return f"ORD-{uuid.uuid4().hex[:12].upper()}"


from typing import Optional, Dict


def create_order(db: Session, *, customer_id: int | None = None, customer_data: Optional[Dict] = None, items: List[dict], shipping: float = 0.0, tax: float = 0.0) -> Order:
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
        raise ValueError("customer_id or customer_data is required to create an order")

    # perform within transaction
    with db.begin():
        # If caller provided customer data (instead of id), create the customer inside this transaction
        if not customer_id and customer_data:
            cust = Customer(
                first_name=customer_data.get("first_name"),
                last_name=customer_data.get("last_name"),
                email=customer_data.get("email"),
                phone=customer_data.get("phone"),
            )
            db.add(cust)
            db.flush()
            customer_id = cust.id

        # Lock and validate inventory rows (simple approach)
        inventory_map = {}
        for it in items:
            inv = None
            if it.get("inventory_id"):
                inv = db.get(Inventory, it["inventory_id"])  # type: ignore[arg-type]
            else:
                # try to find an inventory entry for the animal
                inv = db.execute(
                    select(Inventory).where(Inventory.animal_id == it["animal_id"]).limit(1)
                ).scalars().first()

            if not inv:
                raise ValueError(f"Inventory not found for animal_id={it['animal_id']}")

            if inv.quantity < it["quantity"]:
                raise ValueError(f"Insufficient stock for inventory id {inv.id}")

            inventory_map[it.get("inventory_id") or inv.id] = inv

            unit_price = inv.unit_price if inv.unit_price is not None else Decimal("0.00")
            line_total = Decimal(it["quantity"]) * Decimal(unit_price)
            subtotal += line_total

        # create order
        order = Order(
            order_number=_generate_order_number(db),
            customer_id=customer_id or 0,
            subtotal=subtotal,
            shipping=Decimal(str(shipping)),
            tax=Decimal(str(tax)),
            total=subtotal + Decimal(str(shipping)) + Decimal(str(tax)),
        )
        db.add(order)
        db.flush()  # populate order.id

        # create order items and decrement inventory
        for it in items:
            inv_id = it.get("inventory_id") or next(k for k, v in inventory_map.items() if v.animal_id == it["animal_id"])
            inv = inventory_map[inv_id]

            unit_price = inv.unit_price if inv.unit_price is not None else Decimal("0.00")
            total_price = Decimal(it["quantity"]) * Decimal(unit_price)

            order_item = OrderItem(
                order_id=order.id,
                animal_id=it["animal_id"],
                inventory_id=inv.id,
                quantity=it["quantity"],
                unit_price=unit_price,
                total_price=total_price,
            )
            db.add(order_item)

            # decrement inventory
            inv.quantity = inv.quantity - it["quantity"]
            db.add(inv)

        db.flush()

    # refresh and return
    db.refresh(order)
    return order
