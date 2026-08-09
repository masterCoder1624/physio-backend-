import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    # ── 1. Resolve effective values ───────────────────────────────────────
    target_user_id = req.user_id or str(current_user.id)
    patient_name   = req.name or req.emergency_contact_name
    patient_phone  = req.phone or req.emergency_contact_phone
    injury_type    = req.condition or req.primary_condition

    # ── 2. Required-field validation ──────────────────────────────────────
    missing = []
    if not target_user_id:
        missing.append("user_id")
    if not patient_name:
        missing.append("name")
    if not patient_phone:
        missing.append("phone")
    if not injury_type:
        missing.append("injury_type / condition")

    if missing:
        logger.warning("Create patient rejected – missing fields: %s", missing)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False,
                "message": f"Required fields missing: {', '.join(missing)}",
                "error_code": "MISSING_REQUIRED_FIELDS",
                "missing_fields": missing,
            },
        )

    logger.info(
        "Create patient request user_id=%s name=%s phone=%s appointment_date=%s",
        target_user_id, patient_name, patient_phone, req.appointment_date,
    )

    service = PatientService(db)

    # ── 3. Duplicate check (user_id + phone + name) ──────────────────────
    try:
        already_exists = await service.patient_exists(target_user_id, patient_phone, patient_name)
    except Exception as exc:
        logger.error("Duplicate check failed user_id=%s error=%s", target_user_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "message": "Unable to verify patient record. Please try again.",
                "error_code": "DB_CHECK_FAILED",
            },
        )

    if already_exists:
        logger.warning("Duplicate patient blocked user_id=%s phone=%s", target_user_id, patient_phone)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "message": "Patient already exists",
                "error_code": "DUPLICATE_PATIENT",
            },
        )

    # ── 4. Insert ─────────────────────────────────────────────────────────
    try:
        patient = await service.create_patient_profile(req, target_user_id)
    except Exception as exc:
        err_str = str(exc)
        logger.error("Patient insert failed user_id=%s error=%s", target_user_id, exc, exc_info=True)
        # Belt-and-braces: catch any MongoDB E11000 duplicate that slips through
        if "duplicate key" in err_str.lower() or "E11000" in err_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "message": "Patient already exists",
                    "error_code": "DUPLICATE_PATIENT",
                },
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Unable to save patient. Please try again.",
                "error_code": "PATIENT_CREATE_FAILED",
            },
        )

    logger.info("Patient created patient_id=%s user_id=%s", patient.id, target_user_id)
    return APIResponse(
        message="Patient added successfully",
        data=PatientResponse.model_validate(patient),
    )


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
