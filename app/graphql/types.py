import strawberry
from typing import Optional
from datetime import date


@strawberry.type
class MilkProductionAnalytics:
    period: str
    date: Optional[date]
    total_milk: float
    avg_fat: Optional[float]
    avg_snf: Optional[float]


@strawberry.type
class EventDistribution:
    event_type: str
    count: int


@strawberry.type
class HerdStats:
    status: str
    count: int


@strawberry.type
class BirthVsPurchaseAnalytics:
    period: str
    birth_count: int
    purchase_count: int


@strawberry.type
class GenderDistribution:
    gender: str
    count: int
