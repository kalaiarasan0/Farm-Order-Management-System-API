from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.tracking_tables import PurchaseRawMaterial
from typing import List, Optional

PRICE_FIELDS = {"quantity", "unit_price", "total_price"}

def create_purchase_material(db: Session, data: dict) -> PurchaseRawMaterial:
    try:
        price_details = calculate_price_details(
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
        )

        db.add(purchase_material)
        db.commit()
        db.refresh(purchase_material)
        return purchase_material
    except SQLAlchemyError:
        db.rollback()
        raise

def update_purchase_material(db: Session, purchase_material_id: int, data: dict) -> PurchaseRawMaterial:
    try:
        purchase_material = db.query(PurchaseRawMaterial).filter(PurchaseRawMaterial.id == purchase_material_id).first()
        if purchase_material is None:
            raise ValueError("Purchase material not found")

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
                
            price_details = calculate_price_details(
                quantity=purchase_material.quantity,
                unit_price=purchase_material.unit_price,
                total_price=purchase_material.total_price,
            )

            purchase_material.gross_price = price_details.get("gross_price")
            purchase_material.total_price = price_details.get("total_price")
            purchase_material.discount_amount = price_details.get("discount_amount")
            purchase_material.discount_percentage = price_details.get("discount_percentage")

        db.commit()
        db.refresh(purchase_material)
        return purchase_material

    except SQLAlchemyError:
        db.rollback()
        raise


def calculate_price_details(quantity: Optional[float], unit_price: Optional[float], total_price: Optional[float]):
    # Basic validation
    if quantity is None or unit_price is None:
        raise ValueError("quantity and unit_price are required")

    if quantity <= 0 or unit_price <= 0:
        raise ValueError("quantity and unit_price must be greater than zero")

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
        raise ValueError("total_price cannot be greater than quantity × unit_price")

    discount_percentage = (discount_amount / gross_price) * 100

    return {
        "gross_price": gross_price,
        "total_price": total_price,
        "discount_amount": discount_amount,
        "discount_percentage": round(discount_percentage, 2),
    }

def get_purchase_material(db: Session, material_id: int) -> PurchaseRawMaterial:
    return db.query(PurchaseRawMaterial).filter(PurchaseRawMaterial.id == material_id).first()

def delete_purchase_material(db: Session, material_id: int) -> PurchaseRawMaterial:
    try:
        raw_material = db.query(PurchaseRawMaterial).filter(PurchaseRawMaterial.id == material_id).first()
        if raw_material is None:
            raise ValueError("Raw material not found")
        db.delete(raw_material)
        db.commit()
        return raw_material
    except SQLAlchemyError:
        db.rollback()
        raise

def list_purchase_materials(db: Session, limit: int = 50, offset: int = 0) -> List[PurchaseRawMaterial]:
    return (db.query(PurchaseRawMaterial)
            .limit(limit)
            .offset(offset)
            .all()
        )
