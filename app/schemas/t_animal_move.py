from pydantic import BaseModel, ConfigDict
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

class TrackingMovementResponse(BaseModel):
    
    movement_date: date
    movement_type: str
    notes: str | None
    is_move_to_inventory: int
    tag_id: str
    animal_id: int
    status: str

    model_config = ConfigDict(from_attributes=True)

class TrackingMovementListResponse(BaseModel):
    data: list[TrackingMovementResponse]
    count: int