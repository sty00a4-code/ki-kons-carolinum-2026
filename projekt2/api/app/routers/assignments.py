from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import AssignmentIn, AssignmentOut
from ..security import require_write_key

router = APIRouter(prefix="/assignments", tags=["assignments"])

# Ein Patient ist höchstens einem Studierenden zugeordnet (patient_id unique),
# deshalb ist patient_id zugleich der Schlüssel in der Adresse.
_SELECT = """
    select
        pa.patient_id,
        coalesce(p.pseudonym, p.name) as patient,
        pa.student_id,
        pa.semester,
        pa.note,
        pa.created_at
    from patient_assignments as pa
    join patients as p on pa.patient_id = p.id
"""


@router.get("", response_model=list[AssignmentOut])
def list_assignments(db: Session = Depends(get_db)):
    rows = db.execute(text(_SELECT + " order by pa.patient_id;")).mappings()
    return [AssignmentOut.model_validate(r) for r in rows]


def _load_assignment(patient_id: int, db: Session) -> AssignmentOut:
    query = text(_SELECT + " where pa.patient_id = :patient_id")
    row = db.execute(query, {"patient_id": patient_id}).mappings().first()
    if row is None:
        raise HTTPException(
            status_code=404, detail="Keine Zuordnung für diesen Patienten"
        )
    return AssignmentOut.model_validate(row)


def _check_references(patient_id: int, student_id: int, db: Session) -> None:
    """422 statt Datenbankfehler, wie bei POST /treatment-cases."""
    references = [
        ("patient_id", patient_id, "patients"),
        ("student_id", student_id, "students"),
    ]
    for field, value, table in references:
        row = db.execute(
            text(f"select id from {table} where id = :id"), {"id": value}
        ).first()
        if row is None:
            raise HTTPException(status_code=422, detail=f"Unbekannte {field}: {value}")


@router.put(
    "/{patient_id}",
    response_model=AssignmentOut,
    dependencies=[Depends(require_write_key)],
)
def put_assignment(
    patient_id: int, payload: AssignmentIn, db: Session = Depends(get_db)
):
    """Legt die Zuordnung an oder ersetzt sie vollständig, created_at wird neu gesetzt."""
    _check_references(patient_id, payload.student_id, db)
    db.execute(
        text("delete from patient_assignments where patient_id = :patient_id"),
        {"patient_id": patient_id},
    )
    insert = text(
        """
        insert into patient_assignments (patient_id, student_id, semester, note)
        values (:patient_id, :student_id, :semester, :note)
        """
    )
    db.execute(insert, {**payload.model_dump(), "patient_id": patient_id})
    db.commit()
    return _load_assignment(patient_id, db)


@router.delete(
    "/{patient_id}",
    status_code=204,
    dependencies=[Depends(require_write_key)],
)
def delete_assignment(patient_id: int, db: Session = Depends(get_db)):
    _load_assignment(patient_id, db)
    db.execute(
        text("delete from patient_assignments where patient_id = :patient_id"),
        {"patient_id": patient_id},
    )
    db.commit()
    return Response(status_code=204)
