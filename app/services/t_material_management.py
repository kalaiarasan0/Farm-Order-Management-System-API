from sqlalchemy.exc import SQLAlchemyError
from app.models.tables import PurchaseRawMaterial
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.schemas.users import User

PRICE_FIELDS = {"quantity", "unit_price", "total_price"}


async def create_purchase_material(
    db: AsyncSession, data: dict, current_user: User
) -> PurchaseRawMaterial:
    try:
        price_details = await calculate_price_details(
            quantity=data.get("quantity"),
            unit_price=data.get("unit_price"),
            total_price=data.get("total_price"),
        )

        purchase_material = PurchaseRawMaterial(
            material_name=data.get("material_name"),
            type_of_material=data.get("type_of_material"),
            purchase_date=data.get("purchase_date"),
            notes=data.get("notes"),
            material_expiry_date=data.get("material_expiry_date"),
            quantity=data.get("quantity"),
            unit_price=data.get("unit_price"),
            total_price=price_details.get("total_price"),
            gross_price=price_details.get("gross_price"),
            discount_amount=price_details.get("discount_amount"),
            discount_percentage=price_details.get("discount_percentage"),
            batch_number=data.get("material_batch_number"),
            supplier=data.get("material_supplier"),
            material_description=data.get("material_description"),
            created_by=str(current_user.unique_id),
        )

        db.add(purchase_material)
        await db.commit()
        await db.refresh(purchase_material)
        return purchase_material
    except SQLAlchemyError:
        await db.rollback()
        raise


async def update_purchase_material(
    db: AsyncSession, purchase_material_id: int, data: dict, current_user: User
) -> PurchaseRawMaterial:
    try:
        purchase_material_stmt = select(PurchaseRawMaterial).where(
            PurchaseRawMaterial.id == purchase_material_id
        )
        purchase_material = await db.execute(purchase_material_stmt)
        purchase_material = purchase_material.scalar_one_or_none()
        if purchase_material is None:
            raise HTTPException(status_code=404, detail="Purchase material not found")

        # Track if price fields changes
        price_changed = False
        total_price_explicitly_nullable = False

        for field, value in data.items():
            if field == "total_price" and value is None:
                total_price_explicitly_nullable = True
                price_changed = True
                continue

            if value is None:
                continue

            if hasattr(purchase_material, field):
                setattr(purchase_material, field, value)

                if field in PRICE_FIELDS:
                    price_changed = True

        if price_changed:
            if total_price_explicitly_nullable:
                purchase_material.total_price = None

            price_details = await calculate_price_details(
                quantity=purchase_material.quantity,
                unit_price=purchase_material.unit_price,
                total_price=purchase_material.total_price,
            )

            purchase_material.gross_price = price_details.get("gross_price")
            purchase_material.total_price = price_details.get("total_price")
            purchase_material.discount_amount = price_details.get("discount_amount")
            purchase_material.discount_percentage = price_details.get(
                "discount_percentage"
            )

        purchase_material.updated_by = str(current_user.unique_id)
        await db.commit()
        await db.refresh(purchase_material)
        return purchase_material

    except SQLAlchemyError:
        await db.rollback()
        raise


async def calculate_price_details(
    quantity: Optional[float], unit_price: Optional[float], total_price: Optional[float]
):
    # Basic validation
    if quantity is None or unit_price is None:
        raise HTTPException(
            status_code=400, detail="quantity and unit_price are required"
        )

    if quantity <= 0 or unit_price <= 0:
        raise HTTPException(
            status_code=400, detail="quantity and unit_price must be greater than zero"
        )

    gross_price = quantity * unit_price

    # CASE 2: total_price not provided → no discount
    if total_price is None:
        return {
            "gross_price": gross_price,
            "total_price": gross_price,
            "discount_amount": 0.0,
            "discount_percentage": 0.0,
        }

    # CASE 1: total_price provided → calculate discount
    discount_amount = gross_price - total_price

    # Prevent negative discount (price increased)
    if discount_amount < 0:
        raise HTTPException(
            status_code=400,
            detail="total_price cannot be greater than quantity × unit_price",
        )

    discount_percentage = (discount_amount / gross_price) * 100

    return {
        "gross_price": gross_price,
        "total_price": total_price,
        "discount_amount": discount_amount,
        "discount_percentage": round(discount_percentage, 2),
    }


async def get_purchase_material(
    db: AsyncSession, material_id: int, current_user:User
) -> PurchaseRawMaterial:
    stmt = select(PurchaseRawMaterial).where(PurchaseRawMaterial.id == material_id, PurchaseRawMaterial.created_by == str(current_user.unique_id))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def delete_purchase_material(db: AsyncSession, material_id: int, current_user:User) -> dict:
    try:
        stmt = delete(PurchaseRawMaterial).where(PurchaseRawMaterial.id == material_id, PurchaseRawMaterial.created_by == str(current_user.unique_id))
        raw_material = await db.execute(stmt)
        await db.commit()

        if raw_material.rowcount == 0:
            raise HTTPException(status_code=404, detail="Raw material not found")
        return {"message": "Raw material deleted successfully"}

    except SQLAlchemyError:
        await db.rollback()
        raise


async def list_purchase_materials(
    db: AsyncSession, current_user:User, limit: int = 50, offset: int = 0
) -> List[PurchaseRawMaterial]:
    stmt = select(PurchaseRawMaterial).limit(limit).offset(offset).filter(PurchaseRawMaterial.created_by == str(current_user.unique_id))
    result = await db.execute(stmt)
    return result.scalars().all()
