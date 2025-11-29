from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.customers import CustomerResponse
from app.schemas.addresses import AddressResponse


class OrderItemCreate(BaseModel):
    animal_id: int = Field(..., description="ID of the animal to order")
    inventory_id: int = Field(..., description="Optional inventory item ID")
    quantity: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    customer_id: Optional[int] = Field(None, description="Existing customer ID. If omitted, customer data must be provided")
    customer: Optional[dict] = Field(None, description="Customer details if creating a new customer")
    billing_address_id: Optional[int] = None
    shipping_address_id: Optional[int] = None
    items: List[OrderItemCreate]
    shipping: Optional[float] = 0.0
    tax: Optional[float] = 0.0


class OrderItemResponse(BaseModel):
    id: int
    animal_id: int
    quantity: int
    unit_price: float
    total_price: float


class OrderResponse(BaseModel):
    id: int
    order_number: str
    customer_id: int
    subtotal: float
    shipping: float
    tax: float
    total: float
    items: List[OrderItemResponse]
    # Optional nested objects (strongly typed)
    customer: Optional[CustomerResponse] = None
    billing_address: Optional[AddressResponse] = None
    shipping_address: Optional[AddressResponse] = None
