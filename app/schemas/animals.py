from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProductCreate(BaseModel):
    sku: str
    species: str
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: float
    specs: Optional[str] = None

class ProductResponse(BaseModel):
    product_id: int
    sku: str
    species: str
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: float
    specs: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}