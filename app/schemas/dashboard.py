from typing import Dict, List
from pydantic import BaseModel


class OrderStatusStats(BaseModel):
    status: str
    count: int
    total_amount: float
    total_quantity: int


class DashboardStatsResponse(BaseModel):
    total_animal_types: int
    tracking_animal_status_counts: Dict[str, int]
    order_status_counts: List[OrderStatusStats]
