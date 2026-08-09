import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time, timezone
from pydantic import BaseModel, Field, ConfigDict
from app.models.models import UserRoleEnum, GenderEnum, AppointmentStatusEnum, PaymentStatusEnum, PaymentMethodEnum, DocumentTypeEnum


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MongoBaseDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
    )


class RoleDocument(MongoBaseDocument):
    name: str
    description: Optional[str] = None


class UserDocument(MongoBaseDocument):
    email: str
    hashed_password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: UserRoleEnum = UserRoleEnum.PATIENT
    role_id: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    avatar_url: Optional[str] = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class RefreshTokenDocument(MongoBaseDocument):
    user_id: str
    token: str
    expires_at: datetime
    is_revoked: bool = False


class ClinicDocument(MongoBaseDocument):
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    phone: str
    email: str
    logo_url: Optional[str] = None
    tax_id: Optional[str] = None


class PhysiotherapistDocument(MongoBaseDocument):
    user_id: str
    clinic_id: Optional[str] = None
    specialization: str
    license_number: str
    experience_years: int = 0
    bio: Optional[str] = None


class PatientDocument(MongoBaseDocument):
    user_id: str
    physiotherapist_id: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[GenderEnum] = None
    blood_group: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    primary_condition: str
    medical_history: Optional[str] = None
    appointment_date: Optional[str] = None
    status: str = "active"


class AvailabilityDocument(MongoBaseDocument):
    physiotherapist_id: str
    day_of_week: int
    start_time: str
    end_time: str
    slot_duration_minutes: int = 30


class AppointmentDocument(MongoBaseDocument):
    patient_id: str
    physiotherapist_id: str
    clinic_id: Optional[str] = None
    appointment_date: str
    start_time: str
    end_time: str
    status: AppointmentStatusEnum = AppointmentStatusEnum.SCHEDULED
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None


class ExerciseCategoryDocument(MongoBaseDocument):
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None


class ExerciseDocument(MongoBaseDocument):
    category_id: str
    title: str
    description: str
    body_part: str
    difficulty: str
    equipment_needed: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    instructions: str


class TreatmentProgramExerciseDocument(MongoBaseDocument):
    program_id: str
    exercise_id: str
    sets: int = 3
    repetitions: int = 10
    duration_seconds: Optional[int] = None
    rest_seconds: int = 30
    sequence_order: int = 1
    notes: Optional[str] = None


class TreatmentProgramDocument(MongoBaseDocument):
    title: str
    description: str
    created_by_physio_id: Optional[str] = None
    is_template: bool = True
    is_archived: bool = False
    exercises: List[Dict[str, Any]] = []


class PatientTreatmentPlanDocument(MongoBaseDocument):
    patient_id: str
    program_id: str
    assigned_by_physio_id: str
    start_date: str
    end_date: Optional[str] = None
    is_active: bool = True


class PatientExerciseProgressDocument(MongoBaseDocument):
    patient_id: str
    exercise_id: str
    recorded_date: datetime = Field(default_factory=utc_now)
    completed_sets: int
    completed_reps: int
    pain_score: int
    range_of_motion_deg: Optional[float] = None
    strength_level: Optional[int] = None
    notes: Optional[str] = None
    proof_media_url: Optional[str] = None


class MedicalRecordDocument(MongoBaseDocument):
    patient_id: str
    physiotherapist_id: str
    diagnosis: str
    symptoms: str
    treatment_provided: str
    notes: Optional[str] = None


class PatientNoteDocument(MongoBaseDocument):
    patient_id: str
    author_user_id: str
    note_text: str


class PrescriptionDocument(MongoBaseDocument):
    patient_id: str
    physiotherapist_id: str
    diagnosis: str
    instructions: str
    pdf_url: Optional[str] = None
    qr_code_url: Optional[str] = None


class PaymentDocument(MongoBaseDocument):
    patient_id: str
    appointment_id: Optional[str] = None
    amount: float
    currency: str = "INR"
    status: PaymentStatusEnum = PaymentStatusEnum.PENDING
    payment_method: PaymentMethodEnum = PaymentMethodEnum.RAZORPAY
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None


class InvoiceDocument(MongoBaseDocument):
    patient_id: Optional[str] = None
    physiotherapist_id: Optional[str] = None
    payment_id: Optional[str] = None
    invoice_number: str
    issued_date: datetime = Field(default_factory=utc_now)
    pdf_url: Optional[str] = None
    pdf_filename: Optional[str] = None
    pdf_file_id: Optional[str] = None
    total_amount: float = 0.0
    paid_amount: float = 0.0
    payment_status: str = "pending"
    generation_key: Optional[str] = None


class MessageDocument(MongoBaseDocument):
    sender_id: str
    recipient_id: str
    content: str
    media_url: Optional[str] = None
    is_read: bool = False


class NotificationDocument(MongoBaseDocument):
    user_id: str
    title: str
    message: str
    is_read: bool = False
    notification_type: str = "info"


class DocumentDocument(MongoBaseDocument):
    patient_id: str
    uploader_user_id: str
    title: str
    document_type: DocumentTypeEnum = DocumentTypeEnum.OTHER
    file_url: str
    file_size_bytes: Optional[int] = None


class ActivityLogDocument(MongoBaseDocument):
    user_id: Optional[str] = None
    action: str
    details: Optional[str] = None
    ip_address: Optional[str] = None


class EmailLogDocument(MongoBaseDocument):
    recipient_email: str
    subject: str
    status: str
    error_message: Optional[str] = None


class AuditLogDocument(MongoBaseDocument):
    user_id: Optional[str] = None
    entity_type: str
    entity_id: str
    action: str
    changes_json: Optional[Dict[str, Any]] = None
