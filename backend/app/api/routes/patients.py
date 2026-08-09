import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pymongo.errors import DuplicateKeyError
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database.session import get_db
from app.services.patient_service import PatientService
from app.schemas.patient import PatientCreateRequest, PatientUpdateRequest, PatientResponse
from app.schemas.common import APIResponse, PaginationMeta
from app.schemas.invoice import InvoiceResponse
from app.api.dependencies.auth import get_current_user
from app.models.mongo_models import InvoiceDocument, PatientDocument, UserDocument
from app.repositories.base_repository import BaseRepository

router = APIRouter(prefix="/patients", tags=["Patient Module"])
logger = logging.getLogger("physioverse.patients")


@router.post("", response_model=APIResponse[PatientResponse], status_code=status.HTTP_201_CREATED)
async def create_patient(
    req: PatientCreateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserDocument = Depends(get_current_user),
):
    # ── 1. Resolve display values for validation/logging ──────────────────
    patient_name  = req.name or req.emergency_contact_name
    patient_phone = req.phone or req.emergency_contact_phone
    injury_type   = req.condition or req.primary_condition
    physio_id     = str(current_user.id)   # always the authenticated physio

    # ── 2. Required-field validation ──────────────────────────────────────
    missing = []
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
        "Create patient request physio_id=%s name=%s phone=%s appointment_date=%s",
        physio_id, patient_name, patient_phone, req.appointment_date,
    )

    service = PatientService(db)

    # ── 3. Insert ──────────────────────────────────────────────────────────
    # patient.user_id is a fresh UUID generated inside the service — no
    # pre-check needed because UUIDs are globally unique by construction.
    try:
        patient = await service.create_patient_profile(req, physio_id)
    except HTTPException:
        raise
    except DuplicateKeyError:
        # Belt-and-braces: UUID collision is astronomically unlikely but handled
        logger.warning("DuplicateKeyError at route level physio_id=%s", physio_id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "message": "Patient already exists",
                "error_code": "DUPLICATE_PATIENT",
            },
        )
    except Exception as exc:
        logger.error("Patient insert failed physio_id=%s error=%s", physio_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Unable to save patient. Please try again.",
                "error_code": "PATIENT_CREATE_FAILED",
            },
        )

    logger.info("Patient created patient_id=%s physio_id=%s", patient.id, physio_id)
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


@router.get("/{patient_id}/invoices", response_model=APIResponse[list[InvoiceResponse]])
async def get_patient_invoices(
    patient_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserDocument = Depends(get_current_user),
):
    patient_repo = BaseRepository(PatientDocument, db, collection_name="patients")
    patient = await patient_repo.get_by_id(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "Patient not found",
                "error_code": "PATIENT_NOT_FOUND",
            },
        )

    invoice_repo = BaseRepository(InvoiceDocument, db, collection_name="invoices")
    invoices = await invoice_repo.get_multi(filters={"patient_id": patient_id}, limit=100)
    return APIResponse(
        message="Patient invoices retrieved successfully",
        data=[InvoiceResponse.model_validate(invoice) for invoice in invoices],
        meta=PaginationMeta(page=1, size=len(invoices), total_items=len(invoices), total_pages=1),
    )


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
