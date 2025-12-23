from pydantic import BaseModel
from typing import Optional


class VerifyOrder(BaseModel):
    product_id: int
    customer_id: int
    quantity: int


class VerifyOrderResponse(BaseModel):
    status: str
    message: str
    verification_token: Optional[str] = None


class PlaceOrderRequest(BaseModel):
    verification_token: str
