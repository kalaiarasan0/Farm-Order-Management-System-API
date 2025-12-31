from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.orders import OrderCreate, OrderResponse
from app.services.orders import create_order, get_order_by_id, list_orders
from app.models.tables import Address
from typing import List
from app.models.tables import Customer

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


@router.post("/place-order", response_model=OrderResponse)
def place_order(payload: OrderCreate, db: Session = Depends(get_db)):
    """Place a new order. Validates inventory and persists order records."""
    try:
        # Prefer passing customer data to the service so it can create the customer
        customer_id = payload.customer_id
        customer_data = payload.customer if not payload.customer_id else None

        if not customer_id and not customer_data:
            raise HTTPException(status_code=400, detail="customer_id or customer data is required")

        # MAP ITEMS: product_id -> product_id
        items_data = []
        for item in payload.items:
             i_dict = item.dict()
             i_dict['product_id'] = i_dict.pop('product_id')
             items_data.append(i_dict)

        order = create_order(
            db,
            customer_id=customer_id,
            customer_data=customer_data,
            items=items_data,
            shipping=payload.shipping or 0.0,
            tax=payload.tax or 0.0,
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # build response
    items = []
    for it in order.items:
        items.append(
            {
                "order_item_id": it.id,
                "product_id": it.animal_id,
                "quantity": it.quantity,
                "unit_price": float(it.unit_price),
                "total_price": float(it.total_price),
            }
        )

    return {
        "order_id": order.id,
        "order_number": order.order_number,
        "customer_id": order.customer_id,
        "subtotal": float(order.subtotal),
        "shipping": float(order.shipping),
        "tax": float(order.tax),
        "total": float(order.total),
        "items": items,
    }




@router.get("/list", response_model=List[OrderResponse])
def get_orders(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    """List orders with pagination."""
    orders = list_orders(db, limit=limit, offset=offset)
    results = []
    for order in orders:
        items = []
        for it in order.items:
            items.append(
                {
                    "order_item_id": it.id,
                    "product_id": it.animal_id,
                    "quantity": it.quantity,
                    "unit_price": float(it.unit_price),
                    "total_price": float(it.total_price),
                }
            )

        # nested customer
        customer = None
        if getattr(order, "customer", None):
            c = order.customer
            customer = {
                "customer_id": c.id,
                "first_name": c.first_name,
                "last_name": c.last_name,
                "email": c.email,
                "phone": c.phone,
                "created_at": c.created_at.isoformat() if getattr(c, "created_at", None) is not None else None,
            }

        # billing/shipping
        billing = None
        if getattr(order, "billing_address_id", None):
            addr = db.get(Address, order.billing_address_id)
            if addr:
                billing = {
                    "address_id": addr.id,
                    "label": addr.label,
                    "line1": addr.line1,
                    "line2": addr.line2,
                    "city": addr.city,
                    "state": addr.state,
                    "postal_code": addr.postal_code,
                    "country": addr.country,
                }

        shipping = None
        if getattr(order, "shipping_address_id", None):
            addr = db.get(Address, order.shipping_address_id)
            if addr:
                shipping = {
                    "address_id": addr.id,
                    "label": addr.label,
                    "line1": addr.line1,
                    "line2": addr.line2,
                    "city": addr.city,
                    "state": addr.state,
                    "postal_code": addr.postal_code,
                    "country": addr.country,
                }

        results.append(
            {
                "order_id": order.id,
                "order_number": order.order_number,
                "customer_id": order.customer_id,
                "subtotal": float(order.subtotal),
                "shipping": float(order.shipping),
                "tax": float(order.tax),
                "total": float(order.total),
                "items": items,
                "customer": customer,
                "billing_address": billing,
                "shipping_address": shipping,
            }
        )

    return results


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Get a single order by ID."""
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="order not found")

    items = []
    for it in order.items:
        items.append(
            {
                "order_item_id": it.id,
                "product_id": it.animal_id,
                "quantity": it.quantity,
                "unit_price": float(it.unit_price),
                "total_price": float(it.total_price),
            }
        )

    # Build nested customer info
    customer = None
    if getattr(order, "customer", None):
        c = order.customer
        customer = {
            "customer_id": c.id,
            "first_name": c.first_name,
            "last_name": c.last_name,
            "email": c.email,
            "phone": c.phone,
            "created_at": c.created_at.isoformat() if getattr(c, "created_at", None) is not None else None,
        }

    # Billing and shipping addresses
    billing = None
    if getattr(order, "billing_address_id", None):
        addr = db.get(Address, order.billing_address_id)
        if addr:
            billing = {
                "address_id": addr.id,
                "label": addr.label,
                "line1": addr.line1,
                "line2": addr.line2,
                "city": addr.city,
                "state": addr.state,
                "postal_code": addr.postal_code,
                "country": addr.country,
            }

    shipping = None
    if getattr(order, "shipping_address_id", None):
        addr = db.get(Address, order.shipping_address_id)
        if addr:
            shipping = {
                "address_id": addr.id,
                "label": addr.label,
                "line1": addr.line1,
                "line2": addr.line2,
                "city": addr.city,
                "state": addr.state,
                "postal_code": addr.postal_code,
                "country": addr.country,
            }

    return {
        "order_id": order.id,
        "order_number": order.order_number,
        "customer_id": order.customer_id,
        "subtotal": float(order.subtotal),
        "shipping": float(order.shipping),
        "tax": float(order.tax),
        "total": float(order.total),
        "items": items,
        "customer": customer,
        "billing_address": billing,
        "shipping_address": shipping,
    }

