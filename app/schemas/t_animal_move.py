from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class CreateMovement(BaseModel):
    animal_id : int
    movement_type : Optional[str] = None
    notes : Optional[str] = None

class MovementResponse(BaseModel):
    id : int
    animal_id : int
    movement_type : Optional[str] = None
    movement_date : Optional[date] = None
    notes : Optional[str] = None
    created_at : Optional[datetime] = None
    updated_at : Optional[datetime] = None

class Cronjob(BaseModel):
    run_time: datetime
    data : Optional[list]