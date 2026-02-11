from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from http import HTTPStatus
from app.db import get_async_db
from app.services.customers import (
    get_customer_by_id,
    list_customers,
    get_customer_by_phone,
    get_customer_count,
    create_customer,
    update_customer,
    update_customer_profile_pic,
    delete_customer,
)
from app.schemas.customers import CustomerResponse, CustomerCountResponse
from app.schemas.customers import CustomerCreate, CustomerUpdate
from app.schemas.common import normalize_phone
from app.schemas.addresses import AddressResponse
from app.models.tables import Address, Customer
from sqlalchemy import or_, select
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


@router.get("/count", response_model=CustomerCountResponse)
async def get_customers_count(
    count_type: str,
    name: str = None,
    phone: str = None,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """Return the total number of customers."""
    count = await get_customer_count(db, count_type, name, phone, current_user)
    return {"count": count}


@router.get("/id/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """Get a customer by ID."""
    cust = await get_customer_by_id(db, customer_id, current_user)
    if not cust:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="customer not found"
        )
    return CustomerResponse(
        customer_id=cust.id,
        first_name=cust.first_name,
        last_name=cust.last_name,
        email=cust.email,
        phone=cust.phone,
        created_at=cust.created_at.isoformat()
        if getattr(cust, "created_at", None) is not None
        else None,
    )


@router.get("/by-phone/{phone}", response_model=CustomerResponse)
async def get_customer_by_phone_route(
    phone: str,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """Lookup a customer by phone number."""

    """
    - Validates and normalizes the incoming phone using `normalize_phone`.
    - Calls the service `get_customer_by_phone` with the normalized value.

    Note: when calling, URL-encode `+` as `%2B` or wrap number in quotes in a client that does that for you.
    """

    try:
        normalized = normalize_phone(phone)
    except ValueError as exc:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(exc))

    cust = await get_customer_by_phone(db, normalized, current_user)
    if not cust:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="customer not found"
        )

    return CustomerResponse(
        customer_id=cust.id,
        first_name=cust.first_name,
        last_name=cust.last_name,
        email=cust.email,
        phone=cust.phone,
        created_at=cust.created_at.isoformat()
        if getattr(cust, "created_at", None) is not None
        else None,
    )


@router.get("/list", response_model=List[CustomerResponse])
async def get_customers(
    count_type: str,
    name: str = None,
    phone: str = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """List customers with pagination."""
    customers = await list_customers(
        db, count_type, name, phone, current_user, limit, offset
    )
    out = []
    for c in customers:
        out.append(
            CustomerResponse(
                customer_id=c.id,
                first_name=c.first_name,
                last_name=c.last_name,
                email=c.email,
                phone=c.phone,
                created_at=c.created_at.isoformat()
                if getattr(c, "created_at", None) is not None
                else None,
            )
        )
    return out


@router.post("/create-customer", response_model=CustomerResponse)
async def post_customer(
    payload: CustomerCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """Create a new customer."""
    data = payload.dict()
    cust = await create_customer(db, data, current_user)
    return CustomerResponse(
        customer_id=cust.id,
        first_name=cust.first_name,
        last_name=cust.last_name,
        email=cust.email,
        phone=cust.phone,
        created_at=cust.created_at.isoformat()
        if getattr(cust, "created_at", None) is not None
        else None,
    )


@router.get("/lookup", response_model=list)
async def lookup_customers(
    q: str = "",
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """Search customers by name (first or last) or phone."""
    query = select(Customer).filter(
        or_(
            Customer.first_name.ilike(f"%{q}%"),
            Customer.last_name.ilike(f"%{q}%"),
            Customer.phone.ilike(f"%{q}%"),
        ),
        Customer.created_by == str(current_user.unique_id),
    )
    result = await db.execute(query.limit(20))
    customers = result.scalars().all()

    out = []
    for c in customers:
        out.append(
            {
                "customer_id": c.id,
                "first_name": c.first_name,
                "last_name": c.last_name,
            }
        )

    return out


@router.get("/{customer_id}/addresses", response_model=List[AddressResponse])
async def get_customer_addresses(
    customer_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """Get all addresses for a specific customer."""
    result = await db.execute(
        select(Address).filter(
            Address.customer_id == customer_id,
            Address.created_by == str(current_user.unique_id),
        )
    )
    addresses = result.scalars().all()

    results = []
    for addr in addresses:
        results.append(AddressResponse.model_validate(addr))

    return results


@router.patch("/id/{customer_id}", response_model=CustomerResponse)
async def put_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """Update an existing customer."""
    try:
        # Only include fields that the client actually provided to avoid overwriting
        # existing values with nulls when a field was omitted.
        cust = await update_customer(
            db, customer_id, payload.dict(exclude_unset=True), current_user
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="customer not found")

    return CustomerResponse(
        customer_id=cust.id,
        first_name=cust.first_name,
        last_name=cust.last_name,
        email=cust.email,
        phone=cust.phone,
        created_at=cust.created_at.isoformat()
        if getattr(cust, "created_at", None) is not None
        else None,
    )


@router.patch("/id/{customer_id}/profile-pic", response_model=dict)
async def update_customer_profile_pic_route(
    customer_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """Update a customer's profile picture."""
    return await update_customer_profile_pic(db, customer_id, file, current_user)


@router.delete("/id/{customer_id}", response_model=dict)
async def delete_customer_route(
    customer_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """Delete a customer."""
    return await delete_customer(db, customer_id, current_user)
