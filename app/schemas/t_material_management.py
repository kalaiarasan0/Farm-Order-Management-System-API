from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class CreateMaterial(BaseModel):
    material_name: str
    type_of_material: str
    purchase_date: date
    quantity: int
    unit_price: float
    material_expiry_date: Optional[date] = None
    material_batch_number: Optional[str] = None
    material_supplier: Optional[str] = None
    material_description: Optional[str] = None
    total_price: Optional[float] = None
    notes: Optional[str] = None

class UpdateMaterial(BaseModel):
    material_name: Optional[str] = None
    type_of_material: Optional[str] = None
    purchase_date: Optional[date] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    material_expiry_date: Optional[date] = None
    material_batch_number: Optional[str] = None
    material_supplier: Optional[str] = None
    material_description: Optional[str] = None
    total_price: Optional[float] = None
    notes: Optional[str] = None

class MaterialResponse(BaseModel):
    id: int
    material_name: str
    type_of_material: str
    purchase_date: date
    quantity: int
    unit_price: float
    material_expiry_date: Optional[date] = None
    material_batch_number: Optional[str] = None
    material_supplier: Optional[str] = None
    material_description: Optional[str] = None
    total_price: Optional[float] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    gross_price: float
    discount_amount: float
    discount_percentage: float
    