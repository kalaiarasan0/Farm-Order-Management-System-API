from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.auth import get_current_user
from app.db import get_async_db
from app.services.addresses import get_address_by_id, create_address, update_address
from app.schemas.addresses import AddressCreate, AddressResponse, UpdateAddress
from app.services.addresses import (
    list_addresses,
    list_addresses_by_customer_id,
    list_states,
    district_by_state,
    pincode_by_district,
    delete_address,
)

router = APIRouter(prefix="/api/v1/addresses", tags=["addresses"])

VALID_FIELDS = ["district", "statename", "divisionname"]


@router.get("/id/{address_id}", response_model=AddressResponse)
async def get_address(
    address_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """Get address by ID."""
    addr = await get_address_by_id(db, address_id, current_user)
    if not addr:
        raise HTTPException(status_code=404, detail="address not found")

    if addr.customer_id:
        customer_name = None
        if getattr(addr, "customer", None) is not None:
            # Ensure customer is loaded if not eager loaded (though service should have eager loaded it)
            # But just in case
            # Assuming eager loaded
            fn = getattr(addr.customer, "first_name", "") or ""
            ln = getattr(addr.customer, "last_name", "") or ""
            customer_name = (fn + " " + ln).strip() or None
    return AddressResponse(
        customer_name=customer_name,
        address_id=addr.id,
        label=addr.label,
        line1=addr.line1,
        line2=addr.line2,
        city=addr.city,
        state=addr.state,
        postal_code=addr.postal_code,
        country=addr.country,
        created_at=addr.created_at.isoformat()
        if getattr(addr, "created_at", None) is not None
        else None,
    )


@router.get("/by-customer-id/{customer_id}", response_model=list[AddressResponse])
async def get_addresses_by_customer(
    customer_id: int,
    offset: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """List addresses for a specific customer id."""
    addresses = await list_addresses_by_customer_id(db, customer_id, current_user, offset, limit)
    out = []
    for addr in addresses:
        if addr.customer_id == customer_id:
            customer_name = None
            if getattr(addr, "customer", None) is not None:
                fn = getattr(addr.customer, "first_name", "") or ""
                ln = getattr(addr.customer, "last_name", "") or ""
                customer_name = (fn + " " + ln).strip() or None

            out.append(
                AddressResponse(
                    address_id=addr.id,
                    label=addr.label,
                    line1=addr.line1,
                    line2=addr.line2,
                    city=addr.city,
                    state=addr.state,
                    postal_code=addr.postal_code,
                    country=addr.country,
                    customer_name=customer_name,
                    created_at=addr.created_at.isoformat()
                    if getattr(addr, "created_at", None) is not None
                    else None,
                )
            )
    return out


@router.get("/list", response_model=list[AddressResponse])
async def get_all_addresses(
    offset: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_user)
):
    """List all addresses."""
    addresses = await list_addresses(db, current_user, offset, limit)
    out = []
    for addr in addresses:
        customer_name = None
        if getattr(addr, "customer", None) is not None:
            fn = getattr(addr.customer, "first_name", "") or ""
            ln = getattr(addr.customer, "last_name", "") or ""
            customer_name = (fn + " " + ln).strip() or None

        out.append(
            AddressResponse(
                address_id=addr.id,
                label=addr.label,
                line1=addr.line1,
                line2=addr.line2,
                city=addr.city,
                state=addr.state,
                postal_code=addr.postal_code,
                country=addr.country,
                customer_name=customer_name,
                created_at=addr.created_at.isoformat()
                if getattr(addr, "created_at", None) is not None
                else None,
            )
        )
    return out


@router.post("/create-address", response_model=AddressResponse)
async def post_address(
    payload: AddressCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    data = payload.dict()
    # AddressCreate includes required line1; caller must supply customer_id via dict if desired
    if "customer_id" not in data:
        # allow creating address without customer (but model requires customer_id) -> error
        raise HTTPException(
            status_code=400, detail="customer_id is required in address payload"
        )

    args = data.copy()
    addr = await create_address(db, args, current_user)
    return AddressResponse(
        address_id=addr.id,
        label=addr.label,
        line1=addr.line1,
        line2=addr.line2,
        city=addr.city,
        state=addr.state,
        postal_code=addr.postal_code,
        country=addr.country,
        created_at=addr.created_at.isoformat()
        if getattr(addr, "created_at", None) is not None
        else None,
    )


@router.patch("/id/{address_id}", response_model=AddressResponse)
async def put_address(
    address_id: int,
    payload: UpdateAddress,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    try:
        addr = await update_address(db, address_id, payload.dict(), current_user)
    except ValueError:
        raise HTTPException(status_code=404, detail="address not found")

    return AddressResponse(
        address_id=addr.id,
        label=addr.label,
        line1=addr.line1,
        line2=addr.line2,
        city=addr.city,
        state=addr.state,
        postal_code=addr.postal_code,
        country=addr.country,
    )


@router.get("/states")
async def get_states(
    db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_user)
):
    return await list_states(db)


@router.get("/districts/{state}")
async def get_districts(
    state: str,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    return await district_by_state(db, state)


@router.get("/pincodes/{district}")
async def get_pincodes(
    district: str,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    return await pincode_by_district(db, district)

@router.delete("/id/{address_id}", response_model=dict)
async def delete_address_api(
    address_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_user),
):
    """Delete an address."""
    try:
        address = await delete_address(db, address_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return address
