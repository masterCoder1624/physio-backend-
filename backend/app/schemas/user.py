from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.models import UserRoleEnum


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: UserRoleEnum
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    created_at: datetime


class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
