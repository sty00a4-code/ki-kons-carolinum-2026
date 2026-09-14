"""Pydantic-Modelle für Request/Response. Getrennt von den DB-Queries,
damit die API-Verträge stabil bleiben, auch wenn sich SQL im Hintergrund ändert."""

from datetime import date

from pydantic import BaseModel, ConfigDict


class CategoryProgress(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: str
    student_id: int
    semester: str
    total_points: float
    min: float | None
    done: bool
    progress_pct: float | None


class ClassProgress(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: str
    class_name: str
    student_id: int
    semester: str
    total_points: float
    total_count: int
    min_points_required: float | None
    min_count_required: int | None
    done: bool
    progress_pct: float | None


class PatientCase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    patient_id: int
    patient: str
    category: str
    class_name: str
    region: str | None
    min_points: float | None
    max_points: float | None


class TreatmentCaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    category: str | None
    class_name: str | None
    case_category: str | None
    patient: str | None
    semester: str
    difficulty: float | None
    expected_duration_min: int | None
    actual_duration_min: int | None
    setting: str | None
    treatment_date: date | None
    notes: str | None


class TreatmentCaseIn(BaseModel):
    student_id: int
    class_id: int
    patient_id: int | None = None
    case_category_id: int | None = None
    semester: str
    difficulty: float | None = None
    expected_duration_min: int | None = None
    actual_duration_min: int | None = None
    setting: str | None = None
    treatment_date: date | None = None
    notes: str | None = None


class OsceResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: int
    exam: str
    semester: str | None
    exam_date: date | None
    station: str
    competency: str | None
    points_achieved: float | None
    max_points: float | None
    status: str


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    anon_code: str | None
    enrollment_semester: str | None
