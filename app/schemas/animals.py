from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class CategoryCreate(BaseModel):
    sku: str
    species: str
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: float
    specs: Optional[str] = None

class CategoryResponse(BaseModel):
    category_id: int
    sku: str
    species: str
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: float
    specs: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class CategoryCount(BaseModel):
    count: int

class CategoryUpdate(BaseModel):
    id: int
    sku: Optional[str] = None
    species: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[float] = None
    specs: Optional[str] = None


class CategoryLookup(BaseModel):
    category_id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
