from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.models import PaymentStatusEnum, PaymentMethodEnum


class RazorpayOrderCreateRequest(BaseModel):
    appointment_id: Optional[str] = None
    amount: float
    currency: str = "INR"


class RazorpayVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    appointment_id: Optional[str] = None
    amount: float
    currency: str
    status: PaymentStatusEnum
    payment_method: PaymentMethodEnum
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    created_at: datetime
