from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ExerciseCategoryCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None


class ExerciseCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None


class ExerciseCreateRequest(BaseModel):
    category_id: str
    title: str
    description: str
    body_part: str
    difficulty: str
    equipment_needed: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    instructions: str


class ExerciseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category_id: str
    title: str
    description: str
    body_part: str
    difficulty: str
    equipment_needed: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    instructions: str
    created_at: datetime
    category: Optional[ExerciseCategoryResponse] = None


class ProgramExerciseItem(BaseModel):
    exercise_id: str
    sets: int = 3
    repetitions: int = 10
    duration_seconds: Optional[int] = None
    rest_seconds: int = 30
    sequence_order: int = 1
    notes: Optional[str] = None


class TreatmentProgramCreateRequest(BaseModel):
    title: str
    description: str
    is_template: bool = True
    exercises: List[ProgramExerciseItem] = []


class PatientExerciseProgressCreate(BaseModel):
    exercise_id: str
    completed_sets: int
    completed_reps: int
    pain_score: int
    range_of_motion_deg: Optional[float] = None
    strength_level: Optional[int] = None
    notes: Optional[str] = None
    proof_media_url: Optional[str] = None
