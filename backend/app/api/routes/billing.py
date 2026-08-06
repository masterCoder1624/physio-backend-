import os
import re
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.api.dependencies.auth import get_current_user
from app.models.mongo_models import UserDocument
from app.schemas.common import APIResponse

router = APIRouter(prefix="/billing", tags=["Billing"])


class GeneratePdfRequest(BaseModel):
    patient_name: str = Field(min_length=1, max_length=200)
    description: str = ""
    total_amount: float = 0
    paid_amount: float = 0


@router.post("/generate-pdf", response_model=APIResponse[dict])
async def generate_pdf(
    payload: GeneratePdfRequest,
    request: Request,
    _: UserDocument = Depends(get_current_user),
):
    """Generate an invoice and return a frontend-accessible path and URL."""
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
    return APIResponse(
        message="Invoice PDF generated successfully",
        data={"pdf_path": pdf_path, "pdf_url": str(request.base_url).rstrip("/") + pdf_path},
    )
