from pydantic import BaseModel
from typing import Optional
from app.schemas.animals import ProductResponse
from datetime import datetime

class InventoryCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    location: Optional[str] = None
    status: Optional[str] = "available"
    specs: Optional[str] = None

class InventoryResponse(BaseModel):
    inventory_id: int
    product_id: Optional[int] = None
    quantity: int
    unit_price: float
    location: Optional[str] = None
    status: Optional[str] = None
    specs: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    product: Optional[ProductResponse] = None
    
    model_config = {"from_attributes": True}