from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class CreateEvent(BaseModel):
    animal_id: int
    event_type: str
    event_date: date
    notes: Optional[str] = None

class AnimalEventResponse(BaseModel):
    id: int
    animal_id: int
    animal_name: Optional[str] = None
    animal_species: Optional[str] = None
    event_type: str
    event_date: date
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UpdateAnimalEvent(BaseModel):
    event_type: Optional[str] = None
    event_date: Optional[date] = None
    notes: Optional[str] = None

class UpdateEventNotes(BaseModel):
    notes: str