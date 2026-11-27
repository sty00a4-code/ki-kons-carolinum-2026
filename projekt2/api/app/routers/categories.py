from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from .. import audit
from ..database import get_db
from ..schemas import CategoryOut, CategoryPointsIn, CategoryPointsOut
from ..security import User, any_user, require_roles, staff

router = APIRouter(prefix="/categories", tags=["categories"])
# Alte Form der Punkte-Endpunkte (Identität halb in der URL, halb im Body/Query).
# Wird nur unter den unversionierten Pfaden eingebunden (siehe main.py); die
# Nachfolger stehen unter /students/{id}/categories/{id}/points/{semester}.
legacy_router = APIRouter(prefix="/categories", tags=["categories (veraltet)"])


@router.get("", response_model=list[CategoryOut])
def list_categories(_: User = Depends(any_user), db: Session = Depends(get_db)):
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


@router.get(
    "/{category_id}/points",
    response_model=list[CategoryPointsOut],
    dependencies=[Depends(staff)],
)
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


def upsert_category_points(
    db: Session,
    user: User,
    student_id: int,
    category_id: int,
    semester: str,
    points: float,
    missing_student_status: int = 422,
) -> CategoryPointsOut:
    """Gemeinsame Logik der neuen und der alten PUT-Route. Ein zweiter Aufruf
    für dieselbe Identität ersetzt den Wert (Upsert), addiert also nicht."""
    category = _require_category(category_id, db)
    row = db.execute(
        text("select id from students where id = :id"), {"id": student_id}
    ).first()
    if row is None:
        raise HTTPException(
            status_code=missing_student_status,
            detail=f"Unbekannte student_id: {student_id}",
        )
    key = {"student_id": student_id, "category_id": category_id, "semester": semester}
    before = (
        db.execute(
            text(
                """
                select student_id, category_id, semester, points
                from students_categories
                where student_id = :student_id and category_id = :category_id
                  and semester = :semester
                """
            ),
            key,
        )
        .mappings()
        .first()
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
        {**key, "points": points},
    )
    audit.record(
        db,
        user,
        "update" if before is not None else "create",
        "category_points",
        f"{student_id}/{category_id}/{semester}",
        before=before,
        after={**key, "points": points},
    )
    db.commit()
    return CategoryPointsOut.model_validate(
        {**key, "category": category, "points": points}
    )


def remove_category_points(
    db: Session, user: User, student_id: int, category_id: int, semester: str
) -> None:
    """404, wenn es dafür keinen Eintrag gibt. Klassenpunkte bleiben unberührt."""
    _require_category(category_id, db)
    key = {"student_id": student_id, "category_id": category_id, "semester": semester}
    before = (
        db.execute(
            text(
                """
                select student_id, category_id, semester, points
                from students_categories
                where student_id = :student_id and category_id = :category_id
                  and semester = :semester
                """
            ),
            key,
        )
        .mappings()
        .first()
    )
    if before is None:
        raise HTTPException(
            status_code=404, detail="Kein direkter Kategorie-Punkteeintrag gefunden"
        )
    db.execute(
        text(
            """
            delete from students_categories
            where category_id = :category_id
              and student_id = :student_id
              and semester = :semester
            """
        ),
        key,
    )
    audit.record(
        db, user, "delete", "category_points",
        f"{student_id}/{category_id}/{semester}", before=before,
    )
    db.commit()


@legacy_router.put("/{category_id}/points", response_model=CategoryPointsOut, deprecated=True)
def set_category_points(
    category_id: int,
    payload: CategoryPointsIn,
    user: User = Depends(require_roles("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """VERALTET: stattdessen PUT /students/{id}/categories/{id}/points/{semester}."""
    return upsert_category_points(
        db, user, payload.student_id, category_id, payload.semester, payload.points
    )


@legacy_router.delete("/{category_id}/points", status_code=204, deprecated=True)
def delete_category_points(
    category_id: int,
    student_id: int,
    semester: str,
    user: User = Depends(require_roles("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """VERALTET: stattdessen DELETE /students/{id}/categories/{id}/points/{semester}."""
    remove_category_points(db, user, student_id, category_id, semester)
    return Response(status_code=204)
