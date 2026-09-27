from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import CategoryOut, CategoryPointsIn, CategoryPointsOut
from ..security import require_write_key

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    """Katalog für die UI, z.B. um category_id-Dropdowns zu füllen."""
    rows = db.execute(
        text("select id, name, descr, min_points from categories order by id")
    ).mappings()
    return [CategoryOut.model_validate(r) for r in rows]


def _require_category(category_id: int, db: Session) -> str:
    row = (
        db.execute(
            text("select name from categories where id = :id"), {"id": category_id}
        )
        .mappings()
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Kategorie nicht gefunden")
    return row["name"]


@router.get("/{category_id}/points", response_model=list[CategoryPointsOut])
def list_category_points(category_id: int, db: Session = Depends(get_db)):
    """Direkt an dieser Kategorie gutgeschriebene Punkte (students_categories),
    getrennt von den über Klassen erreichten Punkten - zur Nachvollziehbarkeit,
    was pauschal statt über eine Unterkategorie vergeben wurde."""
    category = _require_category(category_id, db)
    rows = db.execute(
        text(
            """
            select
                sca.student_id,
                sca.category_id,
                :category as category,
                sca.semester,
                sca.points
            from students_categories as sca
            where sca.category_id = :category_id
            order by sca.student_id, sca.semester
            """
        ),
        {"category_id": category_id, "category": category},
    ).mappings()
    return [CategoryPointsOut.model_validate(r) for r in rows]


@router.put(
    "/{category_id}/points",
    response_model=CategoryPointsOut,
    dependencies=[Depends(require_write_key)],
)
def set_category_points(
    category_id: int, payload: CategoryPointsIn, db: Session = Depends(get_db)
):
    """Setzt die Punkte, die ein Student in einem Semester direkt an dieser
    Oberkategorie hat - unabhängig von students_classes. Ein zweiter Aufruf
    für denselben Studenten/dasselbe Semester ersetzt den Wert (Upsert),
    addiert also nicht.

    Damit lässt sich eine Kategorie pauschal bepunkten, ohne eine einzelne
    Klasse (Unterkategorie) darunter anzufassen; /students/{id}/category-progress
    zählt diesen Wert zusätzlich zu den über Klassen erreichten Punkten."""
    category = _require_category(category_id, db)
    row = db.execute(
        text("select id from students where id = :id"), {"id": payload.student_id}
    ).first()
    if row is None:
        raise HTTPException(
            status_code=422, detail=f"Unbekannte student_id: {payload.student_id}"
        )
    db.execute(
        text(
            """
            insert into students_categories (student_id, category_id, semester, points)
            values (:student_id, :category_id, :semester, :points)
            on conflict (student_id, category_id, semester)
            do update set points = excluded.points
            """
        ),
        {**payload.model_dump(), "category_id": category_id},
    )
    db.commit()
    return CategoryPointsOut.model_validate(
        {
            "student_id": payload.student_id,
            "category_id": category_id,
            "category": category,
            "semester": payload.semester,
            "points": payload.points,
        }
    )
