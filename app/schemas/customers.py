from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Annotated
from app.schemas.common import Phone, normalize_phone


# Pydantic v2 style validators using Annotated + Field + field_validator
AnnotatedStrMin1 = Annotated[str, Field(min_length=1)]


class CustomerBase(BaseModel):
    first_name: Optional[AnnotatedStrMin1] = None
    last_name: Optional[AnnotatedStrMin1] = None
    email: Optional[EmailStr] = None
    phone: Optional[Phone] = None

    @field_validator("first_name", "last_name", mode="before")
    def _strip_names(cls, v):
        if v is None:
            return v
        return v.strip()

    @field_validator("phone", mode="before")
    def _normalize_phone(cls, v):
        if v is None:
            return v
        try:
            return normalize_phone(v)
        except ValueError as exc:
            raise ValueError(str(exc))


class CustomerCreate(CustomerBase):
    first_name: AnnotatedStrMin1 = Field(...,
                                         description="Customer first name")
    email: EmailStr = Field(..., description="Valid email address")


class CustomerUpdate(CustomerBase):
    """All fields optional for partial updates but validated when provided."""


class CustomerResponse(BaseModel):
    customer_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    customer_image: Optional[str] = None
    model_config = {"from_attributes": True}


class CustomerCountResponse(BaseModel):
    count: int