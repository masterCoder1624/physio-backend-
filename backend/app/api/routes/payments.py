from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database.session import get_db
from app.services.payment_service import PaymentService
from app.schemas.payment import RazorpayOrderCreateRequest, RazorpayVerifyRequest
from app.schemas.common import APIResponse
from app.api.dependencies.auth import get_current_user
from app.models.mongo_models import UserDocument

router = APIRouter(prefix="/payments", tags=["Payment Module"])


@router.post("/razorpay/create-order", response_model=APIResponse[dict])
async def create_order(
    req: RazorpayOrderCreateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserDocument = Depends(get_current_user),
):
    service = PaymentService(db)
    result = await service.create_razorpay_order(current_user.id, req)
    return APIResponse(message="Razorpay order created successfully", data=result)


@router.post("/razorpay/verify", response_model=APIResponse[dict])
async def verify_payment(
    req: RazorpayVerifyRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserDocument = Depends(get_current_user),
):
    service = PaymentService(db)
    verified = await service.verify_payment_signature(req)
    return APIResponse(message="Payment verified successfully", data={"verified": verified})
