import strawberry
from typing import List, Optional
from datetime import date
from app.graphql.types import (
    MilkProductionAnalytics,
    EventDistribution,
    HerdStats,
    BirthVsPurchaseAnalytics,
    GenderDistribution,
)
from app.graphql.resolvers import (
    get_milk_analytics,
    get_event_distribution,
    get_herd_stats,
    get_birth_vs_purchase,
    get_gender_distribution,
)


@strawberry.type
class Query:
    @strawberry.field
    async def milk_analytics(
        self,
        start_date: date,
        end_date: date,
        animal_id: Optional[int] = None,
        period: str = "DAY",
    ) -> List[MilkProductionAnalytics]:
        return await get_milk_analytics(start_date, end_date, animal_id, period)

    @strawberry.field
    async def event_distribution(
        self, start_date: date, end_date: date
    ) -> List[EventDistribution]:
        return await get_event_distribution(start_date, end_date)

    @strawberry.field
    async def herd_stats(self) -> List[HerdStats]:
        return await get_herd_stats()

    @strawberry.field
    async def birth_vs_purchase(
        self, start_date: date, end_date: date, period: Optional[str] = "MONTH"
    ) -> List[BirthVsPurchaseAnalytics]:
        return await get_birth_vs_purchase(start_date, end_date, period)

    @strawberry.field
    async def gender_distribution(self) -> List[GenderDistribution]:
        return await get_gender_distribution()


schema = strawberry.Schema(query=Query)
