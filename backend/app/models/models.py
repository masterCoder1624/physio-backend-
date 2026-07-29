import enum


class UserRoleEnum(str, enum.Enum):
    ADMIN = "admin"
    PHYSIOTHERAPIST = "physiotherapist"
    PATIENT = "patient"


class GenderEnum(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class AppointmentStatusEnum(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"
    NO_SHOW = "no_show"


class PaymentStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethodEnum(str, enum.Enum):
    RAZORPAY = "razorpay"
    CASH = "cash"
    CARD = "card"
    UPI = "upi"


class DocumentTypeEnum(str, enum.Enum):
    XRAY = "xray"
    MRI = "mri"
    REPORT = "report"
    PRESCRIPTION = "prescription"
    OTHER = "other"
