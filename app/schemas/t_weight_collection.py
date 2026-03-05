from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date


class WeightCollectionCreate(BaseModel):
    animal_tag_id: str  # used to resolve animal_id at service layer
    weight_kg: float
    weight_date: Optional[date] = None
    weight_unit: Optional[str] = "kg"
    notes: Optional[str] = None


class WeightCollectionUpdate(BaseModel):
    weight_kg: Optional[float] = None
    weight_date: Optional[date] = None
    weight_unit: Optional[str] = None
    notes: Optional[str] = None


class WeightCollectionResponse(BaseModel):
    id: int
    animal_id: int
    animal_tag_id: Optional[str] = None
    category_name: Optional[str] = None
    category_species: Optional[str] = None
    weight_kg: float
    weight_date: Optional[date] = None
    weight_unit: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WeightCollectionListResponse(BaseModel):
    count: int
    records: List[WeightCollectionResponse]


# ── Dashboard schemas ─────────────────────────────────────────────────────────


class WeightKPIStats(BaseModel):
    total_animals: int
    avg_weight: float
    max_weight: float


class GrowthTrendPoint(BaseModel):
    tag_id: str
    date: date
    weight_kg: float


class MonthlyAvgPoint(BaseModel):
    month: str  # e.g. "2025-01"
    avg_weight: float


class TopHeavyAnimal(BaseModel):
    tag_id: str
    category_name: Optional[str] = None
    max_weight: float


class WeightBucket(BaseModel):
    bucket_label: str  # e.g. "50–60 kg"
    count: int


class LowGrowthAlert(BaseModel):
    tag_id: str
    category_name: Optional[str] = None
    start_weight: float
    end_weight: float
    growth_kg: float  # can be negative
    months: float
    growth_per_month: float


class WeightDashboardResponse(BaseModel):
    kpi: WeightKPIStats
    growth_trend: List[GrowthTrendPoint]
    monthly_avg: List[MonthlyAvgPoint]
    top_heaviest: List[TopHeavyAnimal]
    weight_distribution: List[WeightBucket]
