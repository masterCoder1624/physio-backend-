from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, model_validator, Field
from app.models.models import GenderEnum
from app.schemas.user import UserResponse


class PatientCreateRequest(BaseModel):
    user_id: Optional[str] = None
    physiotherapist_id: Optional[str] = None
    name: Optional[str] = None
    condition: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    primary_condition: Optional[str] = None
    medical_history: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def map_aliases(cls, data: dict) -> dict:
        if isinstance(data, dict):
            if "name" in data and not data.get("emergency_contact_name"):
                data["emergency_contact_name"] = data["name"]
            if "condition" in data and not data.get("primary_condition"):
                data["primary_condition"] = data["condition"]
            elif "primary_condition" in data and not data.get("condition"):
                data["condition"] = data["primary_condition"]
            if "phone" in data and not data.get("emergency_contact_phone"):
                data["emergency_contact_phone"] = data["phone"]

            if not data.get("primary_condition"):
                data["primary_condition"] = "General Physiotherapy"
        return data


class PatientUpdateRequest(BaseModel):
    physiotherapist_id: Optional[str] = None
    name: Optional[str] = None
    condition: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    primary_condition: Optional[str] = None
    medical_history: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def map_aliases(cls, data: dict) -> dict:
        if isinstance(data, dict):
            if "name" in data:
                data["emergency_contact_name"] = data["name"]
            if "condition" in data:
                data["primary_condition"] = data["condition"]
            if "phone" in data:
                data["emergency_contact_phone"] = data["phone"]
        return data


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: Optional[str] = None
    user_id: str
    physiotherapist_id: Optional[str] = None
    name: Optional[str] = None
    condition: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    primary_condition: str
    medical_history: Optional[str] = None
    created_at: datetime
    user: Optional[UserResponse] = None

    @model_validator(mode="after")
    def populate_aliases(self) -> "PatientResponse":
        self.patient_id = self.id
        if not self.name:
            self.name = self.emergency_contact_name or "Patient"
        if not self.condition:
            self.condition = self.primary_condition
        if not self.phone:
            self.phone = self.emergency_contact_phone
        return self
