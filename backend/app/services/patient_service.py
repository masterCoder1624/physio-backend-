from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
from app.models.mongo_models import PatientDocument, UserDocument
from app.repositories.base_repository import BaseRepository
from app.schemas.patient import PatientCreateRequest, PatientUpdateRequest


class PatientService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.patient_repo = BaseRepository(PatientDocument, db, collection_name="patients")
        self.user_repo = BaseRepository(UserDocument, db, collection_name="users")

    async def patient_exists(self, patient_user_id: str) -> bool:
        """Return True if a patient profile already exists for this patient_user_id."""
        doc = await self.patient_repo.collection.find_one({"user_id": patient_user_id}, {"_id": 1})
        return doc is not None

    async def create_patient_profile(
        self,
        req: PatientCreateRequest,
        physio_user_id: str,
    ) -> PatientDocument:
        """Create a patient profile linked to the creating physiotherapist.

        Architecture:
          patient.user_id           = fresh UUID (unique per patient, NOT the physio's ID)
          patient.physiotherapist_id = physio_user_id (the logged-in physio)

        Patients do not have login accounts in this system.  A new UUID is
        generated as the patient's stable unique identifier so the unique
        user_id index is always satisfied and multiple patients can belong
        to the same physiotherapist.
        """
        # Generate a stable, unique ID for this patient — never use the physio's ID
        patient_user_id = str(uuid.uuid4())

        patient_name = req.name or req.emergency_contact_name or "Patient"
        condition_val = req.condition or req.primary_condition or "General Physiotherapy"
        phone_val = req.phone or req.emergency_contact_phone
        gender_val = req.gender.value if hasattr(req.gender, "value") else req.gender
        now = datetime.now(timezone.utc)

        patient_data = {
            "user_id": patient_user_id,           # unique per patient (fresh UUID)
            "physiotherapist_id": physio_user_id, # the physio who created this patient
            "date_of_birth": str(req.date_of_birth) if req.date_of_birth else None,
            "gender": gender_val,
            "blood_group": req.blood_group,
            "emergency_contact_name": patient_name,
            "emergency_contact_phone": phone_val,
            "primary_condition": condition_val,
            "medical_history": req.medical_history,
            "appointment_date": str(req.appointment_date) if req.appointment_date else None,
            "status": req.status or "active",
            "created_at": now,
            "updated_at": now,
        }
        try:
            return await self.patient_repo.create(patient_data)
        except DuplicateKeyError:
            # Extremely unlikely with a fresh UUID, but handled for safety
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "message": "Patient already exists",
                    "error_code": "DUPLICATE_PATIENT",
                },
            )


    async def get_patient(self, patient_id: str) -> PatientDocument:
        """Get patient by ID."""
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient record not found",
            )
        return patient

    async def get_patient_by_user_id(self, user_id: str) -> PatientDocument:
        """Get patient profile by associated user ID."""
        doc = await self.patient_repo.collection.find_one({"user_id": user_id})
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient profile not found for user",
            )
        return self.patient_repo._doc_to_model(doc)

    async def list_patients(
        self, physio_id: Optional[str] = None, skip: int = 0, limit: int = 20
    ) -> List[PatientDocument]:
        """List patients with optional physio filter."""
        filters = {}
        if physio_id:
            filters["physiotherapist_id"] = physio_id
        return await self.patient_repo.get_multi(skip=skip, limit=limit, filters=filters)

    async def update_patient(self, patient_id: str, req: PatientUpdateRequest) -> PatientDocument:
        """Update patient profile details."""
        update_data = req.model_dump(exclude_unset=True)
        if req.name and "emergency_contact_name" not in update_data:
            update_data["emergency_contact_name"] = req.name
        if req.condition and "primary_condition" not in update_data:
            update_data["primary_condition"] = req.condition
        if req.phone and "emergency_contact_phone" not in update_data:
            update_data["emergency_contact_phone"] = req.phone

        updated = await self.patient_repo.update(patient_id, update_data)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient record not found",
            )
        return updated

    async def delete_patient(self, patient_id: str) -> bool:
        """Delete patient profile by ID."""
        deleted = await self.patient_repo.delete(patient_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient record not found",
            )
        return True
