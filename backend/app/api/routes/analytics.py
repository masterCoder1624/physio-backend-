from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database.session import get_db
from app.services.analytics_service import AnalyticsService
from app.schemas.common import APIResponse
from app.schemas.analytics import AnalyticsSummaryResponse
from app.api.dependencies.auth import get_current_user
from app.models.mongo_models import UserDocument

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=APIResponse[AnalyticsSummaryResponse])
async def get_analytics_summary(
    months: int = Query(6, ge=1, le=12),
    new_patients_days: int = Query(30, ge=1, le=365),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserDocument = Depends(get_current_user),
):
    service = AnalyticsService(db)
    summary = await service.get_physio_summary(
        str(current_user.id), months=months, new_patients_days=new_patients_days
    )
    return APIResponse(message="Analytics summary retrieved", data=AnalyticsSummaryResponse.model_validate(summary))
