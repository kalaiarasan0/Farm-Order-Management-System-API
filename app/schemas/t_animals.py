from pydantic import BaseModel, model_validator, ConfigDict, Field
from typing import Optional, List
from datetime import datetime, date
from app.schemas.enums import AnimalSource, AnimalStatus, OrderStatus
from app.schemas.t_animal_event import AnimalEventResponse
from app.schemas.t_animal_move import MovementResponse

class AnimalCreate(BaseModel):
    category_id: int
    gender: str
    birth_date: Optional[date] = None
    purchase_date: Optional[date] = None
    source: AnimalSource
    source_reference: Optional[str] = None
    purchase_price: Optional[float] = None
    status: AnimalStatus

    @model_validator(mode="after")
    def validate_source_dates(self):
        
        if self.source == AnimalSource.purchase and not self.purchase_date:
            raise ValueError("purchase_date is required when source is 'purchase'")
        
        if self.source == AnimalSource.purchase and not self.purchase_price:
            raise ValueError("purchase_price is required when source is 'purchase'")

        if self.source == AnimalSource.birth and not self.birth_date:
            raise ValueError("birth_date is required when source is 'birth'")
        
        return self
        
class AnimalResponse(BaseModel):
    id: int
    tag_id: str
    category_id: int
    category_name: Optional[str] = None
    gender: str
    birth_date: Optional[date] = None
    purchase_date: Optional[date] = None
    source: AnimalSource
    source_reference: Optional[str] = None
    purchase_price: Optional[float] = None
    status: AnimalStatus
    order_item_id: Optional[int] = None
    order_status: Optional[OrderStatus] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    events: Optional[List[AnimalEventResponse]] = Field(default_factory=list)
    inventory_items: Optional[List[MovementResponse]] = Field(default_factory=list)
    image_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class AnimalUpdate(BaseModel):
    category_id: Optional[int] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    purchase_date: Optional[date] = None
    source: Optional[AnimalSource] = None
    source_reference: Optional[str] = None
    purchase_price: Optional[float] = None
    status: Optional[AnimalStatus] = None

    @model_validator(mode="after")
    def validate_source_dates(self):
        
        if self.source == AnimalSource.purchase and not self.purchase_date:
            raise ValueError("purchase_date is required when source is 'purchase'")

        if self.source == AnimalSource.purchase and not self.purchase_price:
            raise ValueError("purchase_price is required when source is 'purchase'")
        
        if self.source == AnimalSource.birth and not self.birth_date:
            raise ValueError("birth_date is required when source is 'birth'")
        
        return self

class AnimalLookupResponse(BaseModel):
    id: int
    tag_id: str
    category_id: int
    category_name: Optional[str]