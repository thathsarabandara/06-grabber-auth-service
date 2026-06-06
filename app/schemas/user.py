from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserStatus

class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    profile_image: Optional[str] = None

class UserResponse(UserBase):
    id: str
    phone: Optional[str] = None
    profile_image: Optional[str] = None
    status: UserStatus
    created_at: datetime

    class Config:
        from_attributes = True
