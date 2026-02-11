from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.schemas.enums import Gender


class UserBase(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    username: str
    is_active: Optional[bool] = True
    gender: Optional[Gender] = None
    email: Optional[str] = None
    mobile: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class User(UserBase):
    id: int
    password_create_at: Optional[datetime] = None
    profile_file_url: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserSchema(BaseModel):
    id: int
    firstname: str
    lastname: str
    username: str
    is_active: bool
    gender: Optional[Gender] = None
    profile_file_url: Optional[str] = None

    class Config:
        from_attributes = True


class ProfilePicUploadResponse(BaseModel):
    message: str
    profile_file_url: str


class UserPersonalDetails(BaseModel):
    firstname: str
    lastname: str
    gender: Optional[Gender] = None

    class Config:
        from_attributes = True


class UserContactDetails(BaseModel):
    email: str
    mobile: str

    class Config:
        from_attributes = True


class UserProfileDetails(BaseModel):
    profile_file_url: Optional[str] = None

    class Config:
        from_attributes = True
