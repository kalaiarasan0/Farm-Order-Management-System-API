from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import date, datetime, time


class CreateEvent(BaseModel):
    animal_id: int
    event_type: str
    event_date: date
    event_milk_time: Optional[time] = None
    event_milk_quantity: Optional[float] = None
    event_milk_snf: Optional[float] = None
    event_milk_fat: Optional[float] = None
    event_milk_water: Optional[float] = None
    event_milk_rate: Optional[float] = None
    event_milk_session: Optional[str] = None
    total_price: Optional[float] = None
    notes: Optional[str] = None

    @field_validator(
        "event_milk_time",
        "event_milk_quantity",
        "event_milk_snf",
        "event_milk_fat",
        "event_milk_water",
        "event_milk_rate",
        "event_milk_session",
        "total_price",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v


class AnimalEventResponse(BaseModel):
    id: int
    animal_id: int
    animal_tag_id: Optional[str] = None
    category_name: Optional[str] = None
    category_species: Optional[str] = None
    event_type: Optional[str] = None
    event_date: date
    notes: Optional[str] = None
    event_milk_time: Optional[str] = None
    event_milk_quantity: Optional[float] = None
    event_milk_snf: Optional[float] = None
    event_milk_fat: Optional[float] = None
    event_milk_water: Optional[float] = None
    event_milk_rate: Optional[float] = None
    event_milk_session: Optional[str] = None
    total_price: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AnimalEventListResponse(BaseModel):
    count: int
    events: List[AnimalEventResponse]


class EventCreateSuccessResponse(BaseModel):
    message: str


class UpdateAnimalEvent(BaseModel):
    event_type: Optional[str] = None
    event_date: Optional[date] = None
    event_milk_time: Optional[str] = None
    event_milk_quantity: Optional[float] = None
    event_milk_snf: Optional[float] = None
    event_milk_fat: Optional[float] = None
    event_milk_water: Optional[float] = None
    event_milk_rate: Optional[float] = None
    event_milk_session: Optional[str] = None
    total_price: Optional[float] = None
    notes: Optional[str] = None

    @field_validator(
        "event_milk_quantity",
        "event_milk_snf",
        "event_milk_fat",
        "event_milk_water",
        "event_milk_rate",
        "total_price",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v


class UpdateEventNotes(BaseModel):
    notes: str
