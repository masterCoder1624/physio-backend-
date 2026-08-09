import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.api.dependencies.auth import get_current_user
from app.database.session import get_db
from app.models.mongo_models import InvoiceDocument, PatientDocument, UserDocument
from app.repositories.base_repository import BaseRepository
from app.schemas.common import APIResponse

router = APIRouter(prefix="/billing", tags=["Billing"])


class GeneratePdfRequest(BaseModel):
    patient_id: Optional[str] = None
    patient_name: str = Field(min_length=1, max_length=200)
    description: str = ""
    total_amount: float = 0
    paid_amount: float = 0


@router.post("/generate-pdf", response_model=APIResponse[dict])
async def generate_pdf(
    payload: GeneratePdfRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db),
    _: UserDocument = Depends(get_current_user),
):
    """Generate an invoice, persist it for a patient when provided, and return a frontend-accessible PDF URL."""
    if payload.patient_id:
        patient_repo = BaseRepository(PatientDocument, db, collection_name="patients")
        patient = await patient_repo.get_by_id(payload.patient_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "Patient not found",
                    "error_code": "PATIENT_NOT_FOUND",
                },
            )

    filename = f"invoices/{uuid.uuid4().hex}.pdf"
    storage_dir = Path(os.getenv("PDF_STORAGE_DIR", "/tmp/physioverse-pdfs"))
    output_path = storage_dir / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pdf = canvas.Canvas(str(output_path), pagesize=letter)
    pdf.setTitle("PhysioVerse invoice")
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(72, 740, "PhysioVerse Invoice")
    pdf.setFont("Helvetica", 12)
    safe_name = re.sub(r"[\r\n]", " ", payload.patient_name)
    safe_description = re.sub(r"[\r\n]", " ", payload.description)
    pdf.drawString(72, 700, f"Patient: {safe_name}")
    pdf.drawString(72, 678, f"Service: {safe_description}")
    pdf.drawString(72, 656, f"Total: INR {payload.total_amount:.2f}")
    pdf.drawString(72, 634, f"Paid: INR {payload.paid_amount:.2f}")
    pdf.drawString(72, 612, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    pdf.save()

    pdf_path = f"/api/v1/files/{filename}"
    pdf_url = str(request.base_url).rstrip("/") + pdf_path
    invoice_data = {"pdf_path": pdf_path, "pdf_url": pdf_url}

    if payload.patient_id:
        invoice_repo = BaseRepository(InvoiceDocument, db, collection_name="invoices")
        invoice_doc = await invoice_repo.create(
            {
                "patient_id": payload.patient_id,
                "invoice_number": f"INV-{uuid.uuid4().hex[:8].upper()}",
                "pdf_url": pdf_url,
            }
        )
        invoice_data["invoice_id"] = invoice_doc.id
        invoice_data["invoice_number"] = invoice_doc.invoice_number

    return APIResponse(
        message="Invoice PDF generated successfully",
        data=invoice_data,
    )
