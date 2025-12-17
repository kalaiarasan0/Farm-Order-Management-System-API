from pydantic import BaseModel
from typing import Optional


class AddressCreate(BaseModel):
    customer_id: Optional[int] = None
    label: Optional[str] = None
    line1: str
    line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class AddressResponse(BaseModel):
    address_id: int
    label: Optional[str] = None
    line1: str
    line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    customer_name: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    model_config = {"from_attributes": True}
