from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from .. import audit
from ..database import get_db
from ..pagination import Page, fetch_page, page_params
from ..schemas import AssignmentHistoryOut, AssignmentIn, AssignmentOut
from ..security import User, admin_only, staff

# Planungsdaten: lesen dürfen Lehrende und Admins, ändern nur Admins.
router = APIRouter(
    prefix="/assignments", tags=["assignments"], dependencies=[Depends(staff)]
)

# Ein Patient ist höchstens einem Studierenden zugeordnet (patient_id unique),
# deshalb ist patient_id zugleich der Schlüssel in der Adresse.
_SELECT = """
    select
        pa.patient_id,
        coalesce(p.pseudonym, p.name) as patient,
        pa.student_id,
        pa.semester,
        pa.note,
        pa.created_at,
        coalesce(pa.updated_at, pa.created_at) as updated_at
    from patient_assignments as pa
    join patients as p on pa.patient_id = p.id
"""


@router.get("", response_model=list[AssignmentOut])
def list_assignments(
    response: Response,
    page: Page = Depends(page_params),
    db: Session = Depends(get_db),
):
    rows = fetch_page(db, response, _SELECT + " order by pa.patient_id", {}, page)
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


def _archive(db: Session, user: User, old, change: str) -> None:
    """Schreibt die bisherige Fassung in patient_assignment_history."""
    db.execute(
        text(
            """
            insert into patient_assignment_history
                (patient_id, student_id, semester, note, valid_from, change, changed_by)
            values
                (:patient_id, :student_id, :semester, :note, :valid_from, :change, :changed_by)
            """
        ),
        {
            "patient_id": old["patient_id"],
            "student_id": old["student_id"],
            "semester": old["semester"],
            "note": old["note"],
            "valid_from": old["updated_at"] or old["created_at"],
            "change": change,
            "changed_by": user.username,
        },
    )


_CURRENT = """
    select patient_id, student_id, semester, note, created_at, updated_at
    from patient_assignments where patient_id = :patient_id
"""


@router.put("/{patient_id}", response_model=AssignmentOut)
def put_assignment(
    patient_id: int,
    payload: AssignmentIn,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    """Legt die Zuordnung an oder ersetzt sie. Beim Ersetzen bleibt created_at
    erhalten, updated_at wird gesetzt und die vorherige Fassung landet in
    GET /assignments/{patient_id}/history."""
    _check_references(patient_id, payload.student_id, db)
    old = db.execute(text(_CURRENT), {"patient_id": patient_id}).mappings().first()
    values = {**payload.model_dump(), "patient_id": patient_id}
    if old is None:
        db.execute(
            text(
                """
                insert into patient_assignments (patient_id, student_id, semester, note)
                values (:patient_id, :student_id, :semester, :note)
                """
            ),
            values,
        )
    else:
        _archive(db, user, old, "replaced")
        db.execute(
            text(
                """
                update patient_assignments
                set student_id = :student_id, semester = :semester, note = :note,
                    updated_at = current_timestamp
                where patient_id = :patient_id
                """
            ),
            values,
        )
    audit.record(
        db,
        user,
        "create" if old is None else "update",
        "assignment",
        patient_id,
        before=old,
        after=payload.model_dump(),
    )
    db.commit()
    return _load_assignment(patient_id, db)


@router.delete("/{patient_id}", status_code=204)
def delete_assignment(
    patient_id: int,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    _load_assignment(patient_id, db)
    old = db.execute(text(_CURRENT), {"patient_id": patient_id}).mappings().first()
    _archive(db, user, old, "removed")
    db.execute(
        text("delete from patient_assignments where patient_id = :patient_id"),
        {"patient_id": patient_id},
    )
    audit.record(db, user, "delete", "assignment", patient_id, before=old)
    db.commit()
    return Response(status_code=204)


@router.get("/{patient_id}/history", response_model=list[AssignmentHistoryOut])
def get_assignment_history(patient_id: int, db: Session = Depends(get_db)):
    """Frühere Fassungen der Zuordnung eines Patienten, älteste zuerst. Die
    aktuelle Zuordnung steht unter GET /assignments. 404 bei unbekanntem Patienten."""
    if db.execute(
        text("select 1 from patients where id = :id"), {"id": patient_id}
    ).first() is None:
        raise HTTPException(status_code=404, detail="Patient nicht gefunden")
    rows = db.execute(
        text(
            """
            select patient_id, student_id, semester, note, valid_from, valid_to,
                   change, changed_by
            from patient_assignment_history
            where patient_id = :patient_id
            order by id
            """
        ),
        {"patient_id": patient_id},
    ).mappings()
    return [AssignmentHistoryOut.model_validate(r) for r in rows]
