from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import TreatmentCaseIn, TreatmentCaseOut, TreatmentCaseUpdate
from ..security import require_write_key

router = APIRouter(prefix="/treatment-cases", tags=["treatment-cases"])

_SELECT = """
    select
        tc.id as id,
        tc.student_id,
        c.name as category,
        cl.name as class_name,
        cc.name as case_category,
        tc.patient_id,
        coalesce(p.pseudonym, p.name) as patient,
        tc.patient_case_id,
        tc.semester,
        tc.difficulty,
        tc.expected_duration_min,
        tc.actual_duration_min,
        tc.setting,
        tc.treatment_date,
        tc.notes
    from treatment_cases as tc
    left join classes as cl on tc.class_id = cl.id
    left join categories as c on cl.category_id = c.id
    left join case_categories as cc on tc.case_category_id = cc.id
    left join patients as p on tc.patient_id = p.id
"""


@router.get("", response_model=list[TreatmentCaseOut])
def list_treatment_cases(
    student_id: int | None = None,
    patient_id: int | None = None,
    semester: str | None = None,
    db: Session = Depends(get_db),
):
    """Behandlungshistorie, wahlweise nach Student:in und/oder Patient:in
    gefiltert - über ?patient_id= lassen sich alle bisherigen Behandlungen
    eines bestimmten Patienten nachvollziehen (chronologisch sortiert)."""
    query = text(
        _SELECT
        + """
        where (:student_id is null or tc.student_id = :student_id)
          and (:patient_id is null or tc.patient_id = :patient_id)
          and (:semester is null or tc.semester = :semester)
        order by tc.treatment_date, tc.id;
        """
    )
    rows = db.execute(
        query,
        {"student_id": student_id, "patient_id": patient_id, "semester": semester},
    ).mappings()
    return [TreatmentCaseOut.model_validate(r) for r in rows]


@router.get("/{case_id}", response_model=TreatmentCaseOut)
def get_treatment_case(case_id: int, db: Session = Depends(get_db)):
    query = text(_SELECT + " where tc.id = :case_id")
    row = db.execute(query, {"case_id": case_id}).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Behandlungsfall nicht gefunden")
    return TreatmentCaseOut.model_validate(row)


def _check_references(payload: TreatmentCaseIn, db: Session) -> int | None:
    """Prüft die referenzierten IDs vor dem Insert und liefert 422 statt 500.
    Gibt die zu verwendende patient_id zurück (ggf. aus patient_case_id
    übernommen, siehe unten)."""
    references = [
        ("student_id", payload.student_id, "students"),
        ("class_id", payload.class_id, "classes"),
        ("patient_id", payload.patient_id, "patients"),
        ("case_category_id", payload.case_category_id, "case_categories"),
    ]
    for field, value, table in references:
        if value is None:
            continue
        row = db.execute(
            text(f"select id from {table} where id = :id"), {"id": value}
        ).first()
        if row is None:
            raise HTTPException(status_code=422, detail=f"Unbekannte {field}: {value}")

    if payload.patient_case_id is None:
        return payload.patient_id

    case_row = (
        db.execute(
            text("select patient_id from patient_cases where id = :id"),
            {"id": payload.patient_case_id},
        )
        .mappings()
        .first()
    )
    if case_row is None:
        raise HTTPException(
            status_code=422,
            detail=f"Unbekannte patient_case_id: {payload.patient_case_id}",
        )
    if payload.patient_id is not None and payload.patient_id != case_row["patient_id"]:
        raise HTTPException(
            status_code=422,
            detail=(
                f"patient_id ({payload.patient_id}) passt nicht zu "
                f"patient_case_id {payload.patient_case_id} "
                f"(gehört zu Patient {case_row['patient_id']})"
            ),
        )
    # patient_id fehlte im Request -> vom geplanten Fall übernehmen.
    return case_row["patient_id"]


@router.post(
    "",
    response_model=TreatmentCaseOut,
    status_code=201,
    dependencies=[Depends(require_write_key)],
)
def create_treatment_case(payload: TreatmentCaseIn, db: Session = Depends(get_db)):
    """Schreib-Endpoint. X-API-Key schützt ihn, sobald PROJEKT2_API_KEY gesetzt
    ist; Rollen (nur Lehrende) folgen später.

    Wird patient_case_id mitgeschickt, gilt der referenzierte geplante Fall
    (patient_cases) ab sofort als behandelt - sichtbar über
    GET /patients/{patient_id}/cases (Feld treated) und
    GET /treatment-cases?patient_id=... für die volle Historie."""
    resolved_patient_id = _check_references(payload, db)
    insert = text(
        """
        insert into treatment_cases
            (student_id, class_id, case_category_id, patient_id, patient_case_id,
             semester, difficulty, expected_duration_min, actual_duration_min,
             setting, treatment_date, notes)
        values
            (:student_id, :class_id, :case_category_id, :patient_id, :patient_case_id,
             :semester, :difficulty, :expected_duration_min, :actual_duration_min,
             :setting, :treatment_date, :notes)
        """
    )
    result = db.execute(
        insert, {**payload.model_dump(), "patient_id": resolved_patient_id}
    )
    db.commit()
    new_id = result.lastrowid
    return get_treatment_case(new_id, db)


_COLUMNS = (
    "student_id, class_id, case_category_id, patient_id, patient_case_id, "
    "semester, difficulty, expected_duration_min, actual_duration_min, "
    "setting, treatment_date, notes"
)


@router.patch(
    "/{case_id}",
    response_model=TreatmentCaseOut,
    dependencies=[Depends(require_write_key)],
)
def update_treatment_case(
    case_id: int, payload: TreatmentCaseUpdate, db: Session = Depends(get_db)
):
    """Korrigiert einen Behandlungsfall; nur gesendete Felder ändern sich.

    patient_case_id=null löst die Verknüpfung zum geplanten Fall (der gilt
    dann wieder als offen). Wird nur patient_case_id gesetzt, übernimmt die
    API den Patienten vom Fall; sind patient_id und patient_case_id danach
    nicht stimmig, antwortet sie mit 422 wie beim Anlegen."""
    existing = (
        db.execute(
            text(f"select {_COLUMNS} from treatment_cases where id = :id"),
            {"id": case_id},
        )
        .mappings()
        .first()
    )
    if existing is None:
        raise HTTPException(status_code=404, detail="Behandlungsfall nicht gefunden")

    changes = payload.model_dump(exclude_unset=True)
    for field in ("student_id", "class_id", "semester"):
        if field in changes and changes[field] is None:
            raise HTTPException(status_code=422, detail=f"{field} darf nicht null sein")
    if not changes:
        return get_treatment_case(case_id, db)

    merged = dict(existing)
    merged.update(changes)
    if changes.get("patient_case_id") is not None and "patient_id" not in changes:
        # Patient kommt vom neuen Fall, nicht vom bisherigen Wert.
        merged["patient_id"] = None
    try:
        candidate = TreatmentCaseIn.model_validate(merged)
    except ValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    resolved_patient_id = _check_references(candidate, db)
    if "patient_id" in changes or "patient_case_id" in changes:
        changes["patient_id"] = resolved_patient_id

    set_clause = ", ".join(f"{field} = :{field}" for field in changes)
    db.execute(
        text(f"update treatment_cases set {set_clause} where id = :case_id"),
        {**changes, "case_id": case_id},
    )
    db.commit()
    return get_treatment_case(case_id, db)


@router.delete(
    "/{case_id}",
    status_code=204,
    dependencies=[Depends(require_write_key)],
)
def delete_treatment_case(case_id: int, db: Session = Depends(get_db)):
    """Löscht einen Behandlungsfall (z.B. eine Fehleingabe); der verknüpfte
    geplante Fall gilt danach wieder als offen. 409, wenn Bewertungen oder
    erworbene Kompetenzen auf die Behandlung verweisen."""
    get_treatment_case(case_id, db)
    for table, column, label in (
        ("case_assessments", "treatment_case_id", "Bewertungen"),
        ("student_competencies", "treatment_cases_id", "erworbene Kompetenzen"),
    ):
        count = db.execute(
            text(f"select count(*) from {table} where {column} = :id"), {"id": case_id}
        ).scalar()
        if count:
            raise HTTPException(
                status_code=409,
                detail=f"Behandlung hat noch {count} {label} und kann nicht gelöscht werden",
            )
    db.execute(text("delete from treatment_cases where id = :id"), {"id": case_id})
    db.commit()
    return Response(status_code=204)
