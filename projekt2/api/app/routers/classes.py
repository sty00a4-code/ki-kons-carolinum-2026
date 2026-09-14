from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ClassOut, ClassUpdate
from ..security import require_write_key

router = APIRouter(prefix="/classes", tags=["classes"])

# coalesce fängt ein von Hand gesetztes null ab, die Vorgabe der Spalte ist 1.
_SELECT = """
    select
        cl.id,
        cl.name,
        cl.descr,
        cl.min_count,
        cl.min_points,
        cl.difficulty,
        cl.expected_dur_min,
        cl.setting,
        cl.category_id,
        c.name as category,
        coalesce(cl.stretchable, 1) as stretchable,
        cl.max_semesters
    from classes as cl
    join categories as c on cl.category_id = c.id
"""


@router.get("", response_model=list[ClassOut])
def list_classes(db: Session = Depends(get_db)):
    """Katalog für die UI, damit sie die class_ids nicht hart codieren muss."""
    query = text(_SELECT + " order by c.id, cl.id;")
    rows = db.execute(query).mappings()
    return [ClassOut.model_validate(r) for r in rows]


def _load_class(class_id: int, db: Session) -> ClassOut:
    query = text(_SELECT + " where cl.id = :class_id")
    row = db.execute(query, {"class_id": class_id}).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Klasse nicht gefunden")
    return ClassOut.model_validate(row)


@router.patch(
    "/{class_id}",
    response_model=ClassOut,
    dependencies=[Depends(require_write_key)],
)
def update_class(class_id: int, payload: ClassUpdate, db: Session = Depends(get_db)):
    """Planungswerte einer Klasse ändern. Nur gesendete Felder werden
    geschrieben, ein gesendetes null löscht den Wert."""
    _load_class(class_id, db)
    changes = payload.model_dump(exclude_unset=True)
    if changes:
        set_clause = ", ".join(f"{field} = :{field}" for field in changes)
        db.execute(
            text(f"update classes set {set_clause} where id = :class_id"),
            {**changes, "class_id": class_id},
        )
        db.commit()
    return _load_class(class_id, db)
