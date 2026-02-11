from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.customers import CustomerResponse
from app.schemas.addresses import AddressResponse
from datetime import datetime, date
from app.schemas.enums import OrderStatus, AnimalSource, AnimalStatus


class OrderItemCreate(BaseModel):
    category_id: int = Field(..., description="ID of the category (animal) to order")
    inventory_id: int = Field(..., description="Optional inventory item ID")
    quantity: int = Field(..., gt=0)
    discount_value: Optional[float] = Field(0.0, description="Discount value")
    discount_percent: Optional[float] = Field(0.0, description="Discount percentage")
    unit_price: Optional[float] = Field(0.0, description="Unit price")


class OrderCreate(BaseModel):
    customer_id: Optional[int] = Field(
        None,
        description="Existing customer ID. If omitted, customer data must be provided",
    )
    customer: Optional[dict] = Field(
        None, description="Customer details if creating a new customer"
    )
    billing_address_id: Optional[int] = None
    shipping_address_id: Optional[int] = None
    items: List[OrderItemCreate]
    shipping: Optional[float] = 0.0
    tax: Optional[float] = 0.0


class OrderItemResponse(BaseModel):
    order_item_id: int
    category_id: int
    category_name: Optional[str]
    quantity: int
    unit_price: float
    total_price: float
    gross_price: float = Field(0.0, description="Gross price")
    discount_value: float = Field(0.0, description="Discount value")
    discount_percent: float = Field(0.0, description="Discount percentage")


class AnimalResponse(BaseModel):
    animal_id: int
    tag_id: str
    category_id: int
    animal_name: Optional[str]
    gender: str
    birth_date: Optional[date] = None
    purchase_date: Optional[date] = None
    source: AnimalSource
    source_reference: Optional[str] = None
    purchase_price: Optional[float] = None
    status: AnimalStatus
    order_item_id: Optional[int] = None
    order_status: Optional[OrderStatus] = None


class OrderResponse(BaseModel):
    order_id: int
    order_number: str
    customer_id: int
    subtotal: float
    shipping: float
    tax: float
    total: float
    order_status: OrderStatus
    items: List[OrderItemResponse]
    order_date: Optional[datetime] = None
    # Optional nested objects (strongly typed)
    customer: Optional[CustomerResponse] = None
    billing_address: Optional[AddressResponse] = None
    shipping_address: Optional[AddressResponse] = None
    animals: List[AnimalResponse] = []


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    count: int


class OrderItemsStatusUpdate(BaseModel):
    order_item_ids: List[int]
    status: OrderStatus
