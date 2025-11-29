from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AnimalCreate(BaseModel):
    sku: str
    species: str
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: float
    specs: Optional[str] = None

class AnimalResponse(BaseModel):
    id: int
    sku: str
    species: str
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: float
    specs: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}