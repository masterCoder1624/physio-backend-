from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.user import UserResponse


class PhysiotherapistCreateRequest(BaseModel):
    user_id: str
    clinic_id: Optional[str] = None
    specialization: str
    license_number: str
    experience_years: int = 0
    bio: Optional[str] = None


class PhysiotherapistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    clinic_id: Optional[str] = None
    specialization: str
    license_number: str
    experience_years: int
    bio: Optional[str] = None
    created_at: datetime
    user: Optional[UserResponse] = None
