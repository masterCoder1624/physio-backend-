import hmac
import hashlib
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
import razorpay
from app.core.config import settings
from app.models.models import PaymentStatusEnum
from app.models.mongo_models import PaymentDocument, InvoiceDocument
from app.repositories.base_repository import BaseRepository
from app.schemas.payment import RazorpayOrderCreateRequest, RazorpayVerifyRequest


class PaymentService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.payment_repo = BaseRepository(PaymentDocument, db, collection_name="payments")
        self.invoice_repo = BaseRepository(InvoiceDocument, db, collection_name="invoices")
        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID or "test_key", settings.RAZORPAY_KEY_SECRET or "test_secret")
        )

    async def create_razorpay_order(
        self, patient_id: str, req: RazorpayOrderCreateRequest
    ) -> Dict[str, Any]:
        """Create a Razorpay order and save pending payment document in MongoDB."""
        amount_in_paise = int(req.amount * 100)
        order_data = {
            "amount": amount_in_paise,
            "currency": req.currency,
            "payment_capture": 1,
        }

        try:
            order = self.client.order.create(data=order_data)
        except Exception:
            # Fallback mock order if testing keys are unconfigured
            order = {"id": f"order_mock_{patient_id[:8]}", "amount": amount_in_paise, "currency": req.currency}

        payment_dict = {
            "patient_id": patient_id,
            "appointment_id": req.appointment_id,
            "amount": req.amount,
            "currency": req.currency,
            "status": PaymentStatusEnum.PENDING.value,
            "razorpay_order_id": order.get("id"),
        }
        db_payment = await self.payment_repo.create(payment_dict)

        return {
            "payment_id": db_payment.id,
            "razorpay_order_id": order.get("id"),
            "amount": req.amount,
            "currency": req.currency,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        }

    async def verify_payment_signature(self, req: RazorpayVerifyRequest) -> bool:
        """Verify Razorpay payment signature in MongoDB."""
        secret = settings.RAZORPAY_KEY_SECRET or "test_secret"
        generated_signature = hmac.new(
            secret.encode("utf-8"),
            f"{req.razorpay_order_id}|{req.razorpay_payment_id}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if generated_signature != req.razorpay_signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payment signature",
            )

        # Update payment document status
        payments = await self.payment_repo.get_multi(
            filters={"razorpay_order_id": req.razorpay_order_id}
        )
        if payments:
            payment = payments[0]
            await self.payment_repo.update(
                payment.id,
                {
                    "status": PaymentStatusEnum.PAID.value,
                    "razorpay_payment_id": req.razorpay_payment_id,
                    "razorpay_signature": req.razorpay_signature,
                },
            )

            # Create Invoice Document
            invoice_dict = {
                "payment_id": payment.id,
                "invoice_number": f"INV-{payment.id[:8].upper()}",
            }
            await self.invoice_repo.create(invoice_dict)

        return True
