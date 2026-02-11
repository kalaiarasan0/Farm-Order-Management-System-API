from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List
from fastapi import HTTPException, UploadFile
from app.models.tables import Customer
from datetime import datetime
from sqlalchemy import select, func, or_, extract
from app.schemas.users import User
from .users import UPLOAD_DIR, UPLOAD_URL_PREFIX
import os
import shutil
from uuid import uuid4
from app.schemas.common import normalize_phone


async def get_customer_by_id(
    db: AsyncSession, customer_id: int, current_user: User
) -> Customer | None:

    stmt = select(Customer).filter(
        Customer.id == customer_id, Customer.created_by == str(current_user.unique_id)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_customer_by_phone(
    db: AsyncSession, phone: str, current_user: User
) -> Customer | None:
    result = await db.execute(
        select(Customer).filter(
            Customer.phone == phone, Customer.created_by == str(current_user.unique_id)
        )
    )
    return result.scalars().first()


async def get_customer_count(
    db: AsyncSession, count_type, name, phone, current_user: User
) -> int:
    if count_type == "all":
        stmt = select(func.count(Customer.id)).filter(
            Customer.created_by == str(current_user.unique_id)
        )
    elif count_type == "today":
        stmt = select(func.count(Customer.id)).filter(
            func.date(Customer.created_at) == datetime.now().date(),
            Customer.created_by == str(current_user.unique_id),
        )
    elif count_type == "this_month":
        stmt = select(func.count(Customer.id)).filter(
            extract("month", Customer.created_at) == datetime.now().month,
            Customer.created_by == str(current_user.unique_id),
        )
    elif count_type == "this_year":
        stmt = select(func.count(Customer.id)).filter(
            extract("year", Customer.created_at) == datetime.now().year,
            Customer.created_by == str(current_user.unique_id),
        )
    elif count_type == "this_week":
        # Note: 'week' extraction might vary by DB dialect. SQLite usually doesn't strictly support 'week' in extract nicely without custom func.
        # However, for now we will try standard extract. If it fails, fallback might be needed.
        # But commonly in portable code we might just filter by date range.
        # Let's use date range for week to be safe across DBs if possible?
        # Or just stick to previous logic if it worked?
        # Previous logic: Customer.created_at.week == datetime.now().week  <- This implies python side filtering? No, it was SQLAlchemy expression.
        # But SQLAlchemy doesn't have .week on column unless it's a specific dialect extension or hybrid property?
        # Actually standard SQLAlchemy doesn't have .week attribute on Column property.
        # The previous code might have been relying on a specific dialect or it was actually broken/untested?
        # Or `weeks` from `extract`?
        # Let's use `extract('week', ...)`
        stmt = select(func.count(Customer.id)).filter(
            extract("week", Customer.created_at) == datetime.now().isocalendar()[1],
            Customer.created_by == str(current_user.unique_id),
        )
    elif count_type == "name":
        pattern = f"%{name}%"
        stmt = select(func.count(Customer.id)).filter(
            or_(Customer.first_name.ilike(pattern), Customer.last_name.ilike(pattern)),
            Customer.created_by == str(current_user.unique_id),
        )
    elif count_type == "phone":
        pattern = f"%{phone}%"
        stmt = select(func.count(Customer.id)).filter(
            Customer.phone.ilike(pattern),
            Customer.created_by == str(current_user.unique_id),
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid count type")

    result = await db.execute(stmt)
    return result.scalar_one()


async def list_customers(
    db: AsyncSession,
    count_type,
    name,
    phone,
    current_user: User,
    limit: int = 50,
    offset: int = 0,
) -> List[Customer]:
    stmt = select(Customer).filter(Customer.created_by == str(current_user.unique_id))

    if count_type == "all":
        pass
    elif count_type == "today":
        stmt = stmt.filter(func.date(Customer.created_at) == datetime.now().date())
    elif count_type == "this_month":
        stmt = stmt.filter(
            extract("month", Customer.created_at) == datetime.now().month
        )
    elif count_type == "this_year":
        stmt = stmt.filter(extract("year", Customer.created_at) == datetime.now().year)
    elif count_type == "this_week":
        stmt = stmt.filter(
            extract("week", Customer.created_at) == datetime.now().isocalendar()[1]
        )
    elif count_type == "name":
        pattern = f"%{name}%"
        stmt = stmt.filter(
            or_(Customer.first_name.ilike(pattern), Customer.last_name.ilike(pattern))
        )
    elif count_type == "phone":
        pattern = f"%{phone}%"
        stmt = stmt.filter(Customer.phone.ilike(pattern))
    else:
        raise HTTPException(status_code=400, detail="Invalid count type")

    stmt = stmt.order_by(Customer.id.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()


async def create_customer(db: AsyncSession, data: dict, current_user: User) -> Customer:
    """Create a new customer and return it."""
    phone = data.get("phone")
    if phone:
        try:
            phone = normalize_phone(phone)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    cust = Customer(
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        email=data.get("email"),
        phone=phone,
        created_by=str(current_user.unique_id),
    )

    # AsyncSession doesn't support 'in_transaction()' directly in the same way or usage is different.
    # Usually we rely on outer transaction or commit our own if we started it.
    # But usually in FastAPI with Depends(get_async_db), it's a session.
    # We can just add and flush/commit.

    db.add(cust)
    await db.commit()
    await db.refresh(cust)
    return cust


async def update_customer(
    db: AsyncSession, customer_id: int, data: dict, current_user: User
) -> Customer:
    """Update an existing customer and return it. Raises ValueError if not found."""
    cust = await db.get(Customer, customer_id)
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")

    for key in ("first_name", "last_name", "email", "phone"):
        if key in data:
            val = data[key]
            if key == "phone" and val:
                try:
                    val = normalize_phone(val)
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=str(e))
            setattr(cust, key, val)

    cust.updated_by = str(current_user.unique_id)

    await db.commit()
    await db.refresh(cust)
    return cust


async def delete_customer(
    db: AsyncSession, customer_id: int, current_user: User
) -> dict:
    """Delete a customer and return a success message."""
    try:
        cust = await db.get(Customer, customer_id)
        if not cust:
            raise HTTPException(status_code=404, detail="Customer not found")

        await db.delete(cust)
        await db.commit()
        return {"message": "Customer deleted successfully"}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail="Customer is associated with an order"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


async def update_customer_profile_pic(
    db: AsyncSession, customer_id: int, file: UploadFile, current_user: User
) -> dict:
    """Update a customer's profile picture and return the new profile picture URL."""
    cust = await db.get(Customer, customer_id)
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")

    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    ext = os.path.splitext(file.filename)[1].lower()
    filename = f"{uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    customer_image = f"{UPLOAD_URL_PREFIX}/{filename}"
    cust.customer_image = customer_image
    await db.commit()
    await db.refresh(cust)
    return {
        "message": "Profile picture updated successfully",
        "customer_image": customer_image,
    }
