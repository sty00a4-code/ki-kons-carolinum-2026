"""Pydantic-Modelle für Request/Response. Getrennt von den DB-Queries,
damit die API-Verträge stabil bleiben, auch wenn sich SQL im Hintergrund ändert."""

from datetime import date
from typing import Annotated, Any, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from .semester import SEMESTER_PATTERN, validate_semester

# Semester ist ein eigener Typ (Format JJJJSoSe/JJJJWiSe, Jahr 2000 bis 2100);
# die Regeln stehen zentral in semester.py.
Semester = Annotated[
    str, Field(pattern=SEMESTER_PATTERN), AfterValidator(validate_semester)
]
Role = Literal["student", "teacher", "admin"]


class CategoryProgress(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: str
    student_id: int
    # Filterwert oder null, kein Wert aus der Gruppe (siehe routers/students.py).
    semester: str | None
    # Summe aus students_classes (über die Klassen) PLUS students_categories
    # (direkt an der Kategorie gutgeschriebene Punkte).
    total_points: float
    # Herkunft der Summe getrennt ausgewiesen: class_points stammt aus
    # students_classes, direct_points aus students_categories.
    class_points: float = 0
    direct_points: float = 0
    min: float | None
    done: bool
    progress_pct: float | None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    descr: str | None
    min_points: float | None


class CategoryPointsIn(BaseModel):
    student_id: int
    semester: Semester
    points: float


class CategoryPointsValue(BaseModel):
    """Body für PUT /students/{id}/categories/{id}/points/{semester}: die
    Identität (Student, Kategorie, Semester) steht in der URL."""

    points: float


class CategoryPointsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: int
    category_id: int
    category: str
    semester: str
    points: float


class ClassProgress(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: str
    class_name: str
    student_id: int
    # Filterwert oder null, kein Wert aus der Gruppe (siehe routers/students.py).
    semester: str | None
    total_points: float
    total_count: int
    min_points_required: float | None
    min_count_required: int | None
    done: bool
    progress_pct: float | None


class ClassOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    descr: str | None
    min_count: int | None
    min_points: float | None
    difficulty: int | None
    expected_dur_min: int | None
    setting: str | None
    category_id: int
    category: str
    # Planung: darf sich die Leistung über mehrere Semester ziehen, und über
    # höchstens wie viele (1 bis 4, null = keine Vorgabe).
    stretchable: bool
    max_semesters: int | None


class ClassUpdate(BaseModel):
    # Nur gesendete Felder werden geschrieben (exclude_unset im Router).
    difficulty: int | None = Field(default=None, ge=1, le=3)
    expected_dur_min: int | None = Field(default=None, ge=0)
    stretchable: bool | None = None
    max_semesters: int | None = Field(default=None, ge=1, le=4)


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None
    # pseudonym: Kennung statt Klarname. category: über wie viele Semester
    # sich die Behandlung erstreckt (1 bis 4).
    pseudonym: str | None
    age: int | None
    category: int | None
    case_count: int


class PatientCase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    patient: str
    category: str
    class_id: int
    class_name: str
    region: str | None
    min_points: float | None
    max_points: float | None
    # null = Wert der Klasse gilt.
    difficulty: int | None
    expected_dur_min: int | None
    # Behandlungsstatus: treated ist true, sobald ein treatment_cases-Eintrag
    # auf diesen Fall verweist (patient_case_id). Bei mehreren Behandlungen
    # desselben Falls wird die zeitlich letzte gezeigt.
    treated: bool
    treatment_case_id: int | None
    treated_by_student_id: int | None
    treatment_date: date | None


class PatientCaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    class_id: int
    class_name: str
    category: str
    region: str | None
    min_points: float | None
    max_points: float | None
    difficulty: int | None
    expected_dur_min: int | None
    treated: bool
    treatment_case_id: int | None
    treated_by_student_id: int | None
    treatment_date: date | None


class PatientDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None
    pseudonym: str | None
    age: int | None
    category: int | None
    cases: list[PatientCaseOut]


class PatientIn(BaseModel):
    # Leerzeichen am Rand werden entfernt, eine leere Kennung ist ungültig.
    model_config = ConfigDict(str_strip_whitespace=True)

    pseudonym: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    age: int | None = Field(default=None, ge=0, le=120)
    category: int | None = Field(default=None, ge=1, le=4)

    @model_validator(mode="after")
    def _require_pseudonym_or_name(self):
        if self.pseudonym is None and self.name is None:
            raise ValueError("pseudonym oder name muss gesetzt sein")
        return self


class PatientUpdate(BaseModel):
    # Ob nach der Änderung noch pseudonym oder name gesetzt ist, prüft der
    # Router gegen den Bestand.
    model_config = ConfigDict(str_strip_whitespace=True)

    pseudonym: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    age: int | None = Field(default=None, ge=0, le=120)
    category: int | None = Field(default=None, ge=1, le=4)


class PatientCaseIn(BaseModel):
    class_id: int
    region: str | None = Field(default=None, max_length=200)
    min_points: float | None = None
    max_points: float | None = None
    # null = Wert der Klasse gilt.
    difficulty: int | None = Field(default=None, ge=1, le=3)
    expected_dur_min: int | None = Field(default=None, ge=0)


class PatientCaseUpdate(BaseModel):
    class_id: int | None = None
    region: str | None = Field(default=None, max_length=200)
    min_points: float | None = None
    max_points: float | None = None
    difficulty: int | None = Field(default=None, ge=1, le=3)
    expected_dur_min: int | None = Field(default=None, ge=0)


class AssignmentIn(BaseModel):
    student_id: int
    semester: Semester | None = None
    note: str | None = None


class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    patient_id: int
    # Pseudonym, sonst Name.
    patient: str | None
    student_id: int
    semester: str | None
    note: str | None
    created_at: str
    # Zeitpunkt der letzten Änderung; solange nie geändert, gleich created_at.
    updated_at: str | None = None


class AssignmentHistoryOut(BaseModel):
    """Eine frühere Fassung einer Zuordnung (ersetzt oder aufgehoben)."""

    model_config = ConfigDict(from_attributes=True)

    patient_id: int
    student_id: int | None
    semester: str | None
    note: str | None
    valid_from: str | None
    valid_to: str | None
    change: str
    changed_by: str | None


class TreatmentCaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    category: str | None
    class_name: str | None
    case_category: str | None
    patient_id: int | None
    patient: str | None
    # Welcher geplante Fall (patient_cases) hiermit als behandelt markiert
    # wurde. null, wenn die Behandlung ohne vorab geplanten Fall erfasst wurde.
    patient_case_id: int | None
    semester: str
    difficulty: float | None
    expected_duration_min: int | None
    actual_duration_min: int | None
    setting: str | None
    treatment_date: date | None
    notes: str | None


class TreatmentCaseIn(BaseModel):
    # Format und Wertebereiche prüft Pydantic, damit falsche Eingaben 422
    # ergeben und keinen Datenbankfehler.
    student_id: int
    class_id: int
    patient_id: int | None = None
    # Optional: verweist auf einen geplanten Fall (patient_cases.id), um ihn
    # als behandelt zu tracken. Wird patient_id weggelassen, aber
    # patient_case_id gesetzt, übernimmt die API den Patienten vom Fall.
    # Sind beide gesetzt, müssen sie zusammenpassen (422 sonst).
    patient_case_id: int | None = None
    case_category_id: int | None = None
    semester: Semester
    difficulty: float | None = Field(default=None, ge=1, le=3)
    expected_duration_min: int | None = Field(default=None, ge=1)
    actual_duration_min: int | None = Field(default=None, ge=1)
    setting: str | None = None
    treatment_date: date | None = None
    notes: str | None = None


class TreatmentCaseUpdate(BaseModel):
    """PATCH: nur gesendete Felder ändern sich. student_id, class_id und
    semester dürfen nicht auf null gesetzt werden; die übrigen (auch
    patient_case_id, um die Verknüpfung zu lösen) schon."""

    student_id: int | None = None
    class_id: int | None = None
    patient_id: int | None = None
    patient_case_id: int | None = None
    case_category_id: int | None = None
    semester: Semester | None = None
    difficulty: float | None = Field(default=None, ge=1, le=3)
    expected_duration_min: int | None = Field(default=None, ge=1)
    actual_duration_min: int | None = Field(default=None, ge=1)
    setting: str | None = None
    treatment_date: date | None = None
    notes: str | None = None


class TreatmentProgress(BaseModel):
    """Behandlungsstand eines Patienten: wie viele der geplanten Fälle sind
    schon behandelt (Verweis über treatment_cases.patient_case_id)."""

    patient_id: int
    patient: str | None
    planned_cases: int
    treated_cases: int
    open_cases: int
    progress_pct: float | None
    planned_points_min: float
    planned_points_max: float
    treated_points_min: float
    treated_points_max: float
    last_treatment_date: date | None


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


class StudentOverview(BaseModel):
    student: StudentOut
    category_progress: list[CategoryProgress]
    categories_done: int
    categories_open: int
    classes_done: int
    classes_open: int
    treatment_count: int
    assigned_patients: list[str]


# ------------------------------- Anmeldung & Benutzer -------------------------------


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class CurrentUserOut(BaseModel):
    id: int
    username: str
    role: Role
    student_id: int | None
    # jwt | api-key | dev: wie die Anfrage authentifiziert wurde.
    auth: str


class TokenOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: CurrentUserOut


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: Role
    student_id: int | None
    active: bool
    created_at: str | None
    last_login_at: str | None


class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=10, max_length=200)
    role: Role
    student_id: int | None = None

    @model_validator(mode="after")
    def _student_needs_link(self):
        if self.role == "student" and self.student_id is None:
            raise ValueError("student_id ist für die Rolle student Pflicht")
        if self.role != "student" and self.student_id is not None:
            raise ValueError("student_id ist nur für die Rolle student erlaubt")
        return self


class UserUpdate(BaseModel):
    # Nur gesendete Felder werden geändert; die Kombination aus Rolle und
    # student_id prüft der Router gegen den Bestand.
    role: Role | None = None
    student_id: int | None = None
    active: bool | None = None
    password: str | None = Field(default=None, min_length=10, max_length=200)


# ------------------------------------ Audit-Log ------------------------------------


class AuditEntry(BaseModel):
    id: int
    ts: str
    user_id: int | None
    username: str | None
    role: str | None
    action: str
    entity: str
    entity_id: str | None
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    reason: str | None


# ------------------------------------ Analyse-Jobs ------------------------------------


class JobCreate(BaseModel):
    student_id: int


class JobCreated(BaseModel):
    job_id: str
    status: Literal["queued"] = "queued"


class JobOut(BaseModel):
    job_id: str
    student_id: int | None
    status: Literal["queued", "running", "completed", "failed"]
    # 0.0 bis 1.0
    progress: float
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
