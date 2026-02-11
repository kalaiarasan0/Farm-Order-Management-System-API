from pydantic import BaseModel
from typing import Optional


class AddressCreate(BaseModel):
    customer_id: int
    label: str
    line1: str
    line2: str
    city: str
    state: str
    postal_code: str
    country: str


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


class UpdateAddress(BaseModel):
    label: Optional[str] = None
    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None