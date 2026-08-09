from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: Optional[str] = None
    physiotherapist_id: Optional[str] = None
    payment_id: Optional[str] = None
    invoice_number: str
    pdf_url: Optional[str] = None
    total_amount: float = 0.0
    paid_amount: float = 0.0
    payment_status: str = "pending"
    issued_date: Optional[datetime] = None
    created_at: datetime
