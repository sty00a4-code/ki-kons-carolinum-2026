"""Pydantic-Modelle für Request/Response. Getrennt von den DB-Queries,
damit die API-Verträge stabil bleiben, auch wenn sich SQL im Hintergrund ändert."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CategoryProgress(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: str
    student_id: int
    # Filterwert oder null, kein Wert aus der Gruppe (siehe routers/students.py).
    semester: str | None
    total_points: float
    min: float | None
    done: bool
    progress_pct: float | None


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
    semester: str | None = Field(default=None, pattern=r"^[0-9]{4}(SoSe|WiSe)$")
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
    # Format und Wertebereiche prüft Pydantic, damit falsche Eingaben 422
    # ergeben und keinen Datenbankfehler.
    student_id: int
    class_id: int
    patient_id: int | None = None
    case_category_id: int | None = None
    semester: str = Field(pattern=r"^[0-9]{4}(SoSe|WiSe)$")
    difficulty: float | None = Field(default=None, ge=1, le=3)
    expected_duration_min: int | None = Field(default=None, ge=1)
    actual_duration_min: int | None = Field(default=None, ge=1)
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
