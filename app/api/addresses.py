from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.addresses import get_address_by_id, create_address, update_address
from app.schemas.addresses import AddressCreate, AddressResponse
from app.services.addresses import list_addresses, list_addresses_by_customer_id

router = APIRouter(prefix="/api/v1/addresses", tags=["addresses"])


@router.get("/id/{address_id}", response_model=AddressResponse)
def get_address(address_id: int, db: Session = Depends(get_db)):
    """Get address by ID."""
    addr = get_address_by_id(db, address_id)
    if not addr:
        raise HTTPException(status_code=404, detail="address not found")
    return AddressResponse(
        id=addr.id,
        label=addr.label,
        line1=addr.line1,
        line2=addr.line2,
        city=addr.city,
        state=addr.state,
        postal_code=addr.postal_code,
        country=addr.country,
        created_at=addr.created_at.isoformat() if getattr(addr, "created_at", None) is not None else None,
    )

@router.get("/by-customer-id/{customer_id}", response_model=list[AddressResponse])
def get_addresses_by_customer(customer_id: int, db: Session = Depends(get_db)):
    """List addresses for a specific customer id."""
    addresses = list_addresses_by_customer_id(db, customer_id)
    out = []
    for addr in addresses:
        if addr.customer_id == customer_id:
            customer_name = None
            if getattr(addr, "customer", None) is not None:
                fn = getattr(addr.customer, "first_name", "") or ""
                ln = getattr(addr.customer, "last_name", "") or ""
                customer_name = (fn + " " + ln).strip() or None

            out.append(AddressResponse(
                id=addr.id,
                label=addr.label,
                line1=addr.line1,
                line2=addr.line2,
                city=addr.city,
                state=addr.state,
                postal_code=addr.postal_code,
                country=addr.country,
                customer_name=customer_name,
                created_at=addr.created_at.isoformat() if getattr(addr, "created_at", None) is not None else None,
            ))
    return out

@router.get("/list", response_model=list[AddressResponse])
def get_all_addresses(db: Session = Depends(get_db)):
    """List all addresses."""
    addresses = list_addresses(db)
    out = []
    for addr in addresses:
        customer_name = None
        if getattr(addr, "customer", None) is not None:
            fn = getattr(addr.customer, "first_name", "") or ""
            ln = getattr(addr.customer, "last_name", "") or ""
            customer_name = (fn + " " + ln).strip() or None

        out.append(AddressResponse(
            id=addr.id,
            label=addr.label,
            line1=addr.line1,
            line2=addr.line2,
            city=addr.city,
            state=addr.state,
            postal_code=addr.postal_code,
            country=addr.country,
            customer_name=customer_name,
            created_at=addr.created_at.isoformat() if getattr(addr, "created_at", None) is not None else None,
        ))
    return out

@router.post("/create-address", response_model=AddressResponse)
def post_address(payload: AddressCreate, db: Session = Depends(get_db)):
    data = payload.dict()
    # AddressCreate includes required line1; caller must supply customer_id via dict if desired
    if "customer_id" not in data:
        # allow creating address without customer (but model requires customer_id) -> error
        raise HTTPException(status_code=400, detail="customer_id is required in address payload")

    addr = create_address(db, data)
    return AddressResponse(
        id=addr.id,
        label=addr.label,
        line1=addr.line1,
        line2=addr.line2,
        city=addr.city,
        state=addr.state,
        postal_code=addr.postal_code,
        country=addr.country,
        created_at=addr.created_at.isoformat() if getattr(addr, "created_at", None) is not None else None,
    )


@router.put("/id/{address_id}", response_model=AddressResponse)
def put_address(address_id: int, payload: AddressCreate, db: Session = Depends(get_db)):
    try:
        addr = update_address(db, address_id, payload.dict())
    except ValueError:
        raise HTTPException(status_code=404, detail="address not found")

    return AddressResponse(
        id=addr.id,
        label=addr.label,
        line1=addr.line1,
        line2=addr.line2,
        city=addr.city,
        state=addr.state,
        postal_code=addr.postal_code,
        country=addr.country,
    )
