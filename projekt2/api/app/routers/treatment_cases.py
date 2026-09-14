from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import TreatmentCaseIn, TreatmentCaseOut
from ..security import require_write_key

router = APIRouter(prefix="/treatment-cases", tags=["treatment-cases"])

_SELECT = """
    select
        tc.id as id,
        tc.student_id,
        c.name as category,
        cl.name as class_name,
        cc.name as case_category,
        coalesce(p.pseudonym, p.name) as patient,
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
    semester: str | None = None,
    db: Session = Depends(get_db),
):
    query = text(
        _SELECT
        + """
        where (:student_id is null or tc.student_id = :student_id)
          and (:semester is null or tc.semester = :semester)
        order by tc.treatment_date, tc.id;
        """
    )
    rows = db.execute(query, {"student_id": student_id, "semester": semester}).mappings()
    return [TreatmentCaseOut.model_validate(r) for r in rows]


@router.get("/{case_id}", response_model=TreatmentCaseOut)
def get_treatment_case(case_id: int, db: Session = Depends(get_db)):
    query = text(_SELECT + " where tc.id = :case_id")
    row = db.execute(query, {"case_id": case_id}).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Behandlungsfall nicht gefunden")
    return TreatmentCaseOut.model_validate(row)


def _check_references(payload: TreatmentCaseIn, db: Session) -> None:
    """Prüft die referenzierten IDs vor dem Insert und liefert 422 statt 500."""
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


@router.post(
    "",
    response_model=TreatmentCaseOut,
    status_code=201,
    dependencies=[Depends(require_write_key)],
)
def create_treatment_case(payload: TreatmentCaseIn, db: Session = Depends(get_db)):
    """Schreib-Endpoint. X-API-Key schützt ihn, sobald PROJEKT2_API_KEY gesetzt
    ist; Rollen (nur Lehrende) folgen später."""
    _check_references(payload, db)
    insert = text(
        """
        insert into treatment_cases
            (student_id, class_id, case_category_id, patient_id, semester,
             difficulty, expected_duration_min, actual_duration_min,
             setting, treatment_date, notes)
        values
            (:student_id, :class_id, :case_category_id, :patient_id, :semester,
             :difficulty, :expected_duration_min, :actual_duration_min,
             :setting, :treatment_date, :notes)
        """
    )
    result = db.execute(insert, payload.model_dump())
    db.commit()
    new_id = result.lastrowid
    return get_treatment_case(new_id, db)
