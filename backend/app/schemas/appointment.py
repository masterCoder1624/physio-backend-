from typing import Optional
from datetime import date, time, datetime
from pydantic import BaseModel, ConfigDict
from app.models.models import AppointmentStatusEnum


class AppointmentCreateRequest(BaseModel):
    patient_id: str
    physiotherapist_id: str
    clinic_id: Optional[str] = None
    appointment_date: date
    start_time: time
    end_time: time
    notes: Optional[str] = None


class AppointmentUpdateRequest(BaseModel):
    appointment_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    status: Optional[AppointmentStatusEnum] = None
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    physiotherapist_id: str
    clinic_id: Optional[str] = None
    appointment_date: date
    start_time: time
    end_time: time
    status: AppointmentStatusEnum
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime


class AvailabilityCreateRequest(BaseModel):
    physiotherapist_id: str
    day_of_week: int
    start_time: time
    end_time: time
    slot_duration_minutes: int = 30
