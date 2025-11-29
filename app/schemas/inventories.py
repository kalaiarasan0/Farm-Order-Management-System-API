from pydantic import BaseModel
from typing import Optional
from app.schemas.animals import AnimalResponse
from datetime import datetime

class InventoryCreate(BaseModel):
    animal_id: int
    quantity: int
    unit_price: float
    location: Optional[str] = None
    status: Optional[str] = "available"
    specs: Optional[str] = None

class InventoryResponse(BaseModel):
    id: int
    animal_id: Optional[int] = None
    quantity: int
    unit_price: float
    location: Optional[str] = None
    status: Optional[str] = None
    specs: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    animal: Optional[AnimalResponse] = None
    
    model_config = {"from_attributes": True}