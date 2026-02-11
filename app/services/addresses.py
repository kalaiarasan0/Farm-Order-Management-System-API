from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional
from sqlalchemy import func, select
from app.models.tables import Address, Customer, PostOffice
from app.schemas.users import User
from sqlalchemy.exc import IntegrityError


async def get_address_by_id(db: AsyncSession, address_id: int, current_user: User) -> Optional[Address]:
    # Need to load customer if accessed later (like in API checks)
    # The API accesses addr.customer.first_name
    # So we should eager load customer
    result = await db.execute(
        select(Address)
        .options(selectinload(Address.customer))
        .where(Address.id == address_id, Address.created_by == str(current_user.unique_id))
    )
    return result.scalar_one_or_none()


async def create_address(db: AsyncSession, data: dict, current_user: User) -> Address:
    try:
        check_customer = await db.get(Customer, data.get("customer_id"))
        if not check_customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        addr = Address(
            customer_id=data.get("customer_id"),
            label=data.get("label"),
            line1=data.get("line1"),
            line2=data.get("line2"),
            city=data.get("city"),
            state=data.get("state"),
            postal_code=data.get("postal_code"),
            country=data.get("country", ""),
            created_by=str(current_user.unique_id),
        )
        db.add(addr)
        await db.commit()
        await db.refresh(addr)
        return addr
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


async def update_address(
    db: AsyncSession, address_id: int, data: dict, current_user: User
) -> Address:
    try:
        addr = await db.get(Address, address_id)
        if not addr:
            raise HTTPException(status_code=404, detail="Address not found")

        # for key in ("label", "line1", "line2", "city", "state", "postal_code", "country"):
        #     if key in data:
        #         setattr(addr, key, data[key])

        for field, value in data.items():
            if value is None:
                continue
            if hasattr(addr, field):
                setattr(addr, field, value)

        addr.updated_by = str(current_user.unique_id)

        await db.commit()
        await db.refresh(addr)
        return addr
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


async def list_addresses(db: AsyncSession, current_user: User, offset: int, limit: int) -> list[Address]:
    # eager-load customer to avoid N+1 when returning customer name in API
    result = await db.execute(
        select(Address)
        .options(selectinload(Address.customer))
        .filter(Address.created_by == str(current_user.unique_id))
        .offset(offset)
        .limit(limit)
        .order_by(Address.id.desc())
    )
    return result.scalars().all()


async def list_addresses_by_customer_id(
    db: AsyncSession, customer_id: int, current_user: User, offset: int, limit: int
) -> list[Address]:
    result = await db.execute(
        select(Address)
        .options(selectinload(Address.customer))
        .filter(Address.customer_id == customer_id, Address.created_by == str(current_user.unique_id))
        .offset(offset)
        .limit(limit)
        .order_by(Address.id.desc())
    )
    return result.scalars().all()


async def list_states(db: AsyncSession) -> list[str]:
    stmt = (
        select(func.distinct(PostOffice.statename))
        .where(PostOffice.statename.isnot(None))
        .order_by(PostOffice.statename)
    )

    result = await db.execute(stmt)
    return [row[0] for row in result.all()]


async def district_by_state(db: AsyncSession, state: str) -> list[str]:
    stmt = (
        select(func.distinct(PostOffice.district))
        .where(
            func.upper(PostOffice.statename) == state.upper(),
            PostOffice.district.isnot(None),
        )
        .order_by(PostOffice.district)
    )

    result = await db.execute(stmt)
    return [row[0] for row in result.all()]


async def pincode_by_district(db: AsyncSession, district: str) -> list[str]:
    stmt = (
        select(func.distinct(PostOffice.pincode))
        .where(
            func.upper(PostOffice.district) == district.upper(),
            PostOffice.pincode.isnot(None),
        )
        .order_by(PostOffice.pincode)
    )

    result = await db.execute(stmt)
    return [row[0] for row in result.all()]


async def delete_address(db: AsyncSession, address_id: int, current_user: User) -> dict:
    try:
        address = await db.get(Address, address_id)
        if not address:
            raise HTTPException(status_code=404, detail="Address not found")

        await db.delete(address)
        await db.commit()
        return {"message": "Address deleted successfully"}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Address is associated with an order")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Async check requires async run
    pass
