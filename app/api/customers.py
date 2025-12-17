from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from http import HTTPStatus
from app.db import get_db
from app.services.customers import get_customer_by_id, list_customers, get_customer_by_phone, get_customer_count, create_customer, update_customer
from app.schemas.customers import CustomerResponse, CustomerCountResponse
from app.schemas.customers import CustomerCreate, CustomerUpdate
from app.schemas.common import normalize_phone


router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


@router.get("/count", response_model=CustomerCountResponse)
def get_customers_count(db: Session = Depends(get_db)):
    """Return the total number of customers."""
    count = get_customer_count(db)
    return {"count":count}


@router.get("/id/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """ Get a customer by ID."""
    cust = get_customer_by_id(db, customer_id)
    if not cust:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="customer not found")
    return CustomerResponse(
        customer_id=cust.id,
        first_name=cust.first_name,
        last_name=cust.last_name,
        email=cust.email,
        phone=cust.phone,
        created_at=cust.created_at.isoformat() if getattr(
            cust, "created_at", None) is not None else None,
    )


@router.get("/by-phone/{phone}", response_model=CustomerResponse)
def get_customer_by_phone_route(phone: str, db: Session = Depends(get_db)):
    """Lookup a customer by phone number."""

    """    
    - Validates and normalizes the incoming phone using `normalize_phone`.
    - Calls the service `get_customer_by_phone` with the normalized value.

    Note: when calling, URL-encode `+` as `%2B` or wrap number in quotes in a client that does that for you.
    """

    try:
        normalized = normalize_phone(phone)
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail=str(exc))

    cust = get_customer_by_phone(db, normalized)
    if not cust:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="customer not found")

    return CustomerResponse(
        customer_id=cust.id,
        first_name=cust.first_name,
        last_name=cust.last_name,
        email=cust.email,
        phone=cust.phone,
        created_at=cust.created_at.isoformat() if getattr(
            cust, "created_at", None) is not None else None,
    )


@router.get("/list", response_model=List[CustomerResponse])
def get_customers(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    """List customers with pagination."""
    customers = list_customers(db, limit=limit, offset=offset)
    out = []
    for c in customers:
        out.append(
            CustomerResponse(
                customer_id=c.id,
                first_name=c.first_name,
                last_name=c.last_name,
                email=c.email,
                phone=c.phone,
                created_at=c.created_at.isoformat() if getattr(
                    c, "created_at", None) is not None else None,
            )
        )
    return out


@router.post("/create-customer", response_model=CustomerResponse)
def post_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    """Create a new customer."""
    data = payload.dict()
    cust = create_customer(db, data)
    return CustomerResponse(
        customer_id=cust.id,
        first_name=cust.first_name,
        last_name=cust.last_name,
        email=cust.email,
        phone=cust.phone,
        created_at=cust.created_at.isoformat() if getattr(
            cust, "created_at", None) is not None else None,
    )


@router.put("/id/{customer_id}", response_model=CustomerResponse)
def put_customer(customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db)):
    """Update an existing customer."""
    try:
        # Only include fields that the client actually provided to avoid overwriting
        # existing values with nulls when a field was omitted.
        cust = update_customer(
            db, customer_id, payload.dict(exclude_unset=True))
    except ValueError:
        raise HTTPException(status_code=404, detail="customer not found")

    return CustomerResponse(
        customer_id=cust.id,
        first_name=cust.first_name,
        last_name=cust.last_name,
        email=cust.email,
        phone=cust.phone,
        created_at=cust.created_at.isoformat() if getattr(
            cust, "created_at", None) is not None else None,
    )
