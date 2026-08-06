import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database.session import get_db
from app.services.patient_service import PatientService
from app.schemas.patient import PatientCreateRequest, PatientUpdateRequest, PatientResponse
from app.schemas.common import APIResponse, PaginationMeta
from app.api.dependencies.auth import get_current_user
from app.models.mongo_models import UserDocument

router = APIRouter(prefix="/patients", tags=["Patient Module"])
logger = logging.getLogger("physioverse.patients")


@router.post("", response_model=APIResponse[PatientResponse], status_code=status.HTTP_201_CREATED)
async def create_patient(
    req: PatientCreateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserDocument = Depends(get_current_user),
):
    logger.info(
        "Create patient request user_id=%s name_present=%s phone_present=%s appointment_date=%s",
        current_user.id,
        bool(req.name or req.emergency_contact_name),
        bool(req.phone or req.emergency_contact_phone),
        req.appointment_date,
    )
    service = PatientService(db)
    patient = await service.create_patient_profile(req, current_user.id)
    logger.info("Patient created patient_id=%s user_id=%s", patient.id, current_user.id)
    return APIResponse(message="Patient added successfully", data=PatientResponse.model_validate(patient))


@router.get("", response_model=APIResponse[List[PatientResponse]])
async def list_patients(
    physio_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserDocument = Depends(get_current_user),
):
    service = PatientService(db)
    skip = (page - 1) * size
    patients = await service.list_patients(physio_id=physio_id, skip=skip, limit=size)
    total = len(patients)
    meta = PaginationMeta(page=page, size=size, total_items=total, total_pages=1)
    return APIResponse(
        message="Patients retrieved successfully",
        data=[PatientResponse.model_validate(p) for p in patients],
        meta=meta,
    )


@router.get("/{patient_id}", response_model=APIResponse[PatientResponse])
async def get_patient(
    patient_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserDocument = Depends(get_current_user),
):
    service = PatientService(db)
    patient = await service.get_patient(patient_id)
    return APIResponse(message="Patient details retrieved", data=PatientResponse.model_validate(patient))


@router.put("/{patient_id}", response_model=APIResponse[PatientResponse])
async def update_patient(
    patient_id: str,
    req: PatientUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserDocument = Depends(get_current_user),
):
    service = PatientService(db)
    patient = await service.update_patient(patient_id, req)
    return APIResponse(message="Patient details updated", data=PatientResponse.model_validate(patient))


@router.delete("/{patient_id}", response_model=APIResponse[dict])
async def delete_patient(
    patient_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserDocument = Depends(get_current_user),
):
    service = PatientService(db)
    await service.delete_patient(patient_id)
    return APIResponse(
        message="Patient deleted successfully",
        data={"message": "Patient deleted successfully", "patient_id": patient_id},
    )
