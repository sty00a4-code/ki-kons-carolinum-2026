from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import CategoryProgress, ClassProgress, StudentOut

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=list[StudentOut])
def list_students(db: Session = Depends(get_db)):
    rows = db.execute(text("select id, anon_code, enrollment_semester from students order by id")).mappings()
    return [StudentOut.model_validate(r) for r in rows]


@router.get("/{student_id}/category-progress", response_model=list[CategoryProgress])
def get_category_progress(
    student_id: int,
    semester: str | None = None,
    db: Session = Depends(get_db),
):
    """Fortschritt pro Kategorie für einen Studenten (identisch zur Streamlit-Query)."""
    query = text(
        """
        select
            c.name as category,
            sc.student_id,
            sc.semester,
            sum(sc.points) as total_points,
            c.min_points as min,
            (sum(sc.points) >= c.min_points) as done,
            case
                when c.min_points > 0 then
                    100.0 * cast(sum(sc.points) as real) / c.min_points
                else null
            end as progress_pct
        from students_classes as sc
        join classes as cl on sc.class_id = cl.id
        join categories as c on cl.category_id = c.id
        where sc.student_id = :student_id
          and (:semester is null or sc.semester = :semester)
        group by c.id, sc.student_id
        order by c.id;
        """
    )
    rows = db.execute(query, {"student_id": student_id, "semester": semester}).mappings()
    return [CategoryProgress.model_validate(r) for r in rows]


@router.get("/{student_id}/class-progress", response_model=list[ClassProgress])
def get_class_progress(
    student_id: int,
    semester: str | None = None,
    db: Session = Depends(get_db),
):
    """Feingranulare Sicht: Fortschritt pro einzelner Klasse."""
    query = text(
        """
        select
            c.name as category,
            cl.name as class_name,
            sc.student_id,
            sc.semester,
            sum(sc.points) as total_points,
            sum(sc.count) as total_count,
            cl.min_points as min_points_required,
            cl.min_count as min_count_required,
            (
                (cl.min_points is null or sum(sc.points) >= cl.min_points)
                and (cl.min_count is null or sum(sc.count) >= cl.min_count)
            ) as done,
            case
                when cl.min_points > 0 then
                    100.0 * cast(sum(sc.points) as real) / cl.min_points
                else null
            end as progress_pct
        from students_classes as sc
        join classes as cl on sc.class_id = cl.id
        join categories as c on cl.category_id = c.id
        where sc.student_id = :student_id
          and (:semester is null or sc.semester = :semester)
        group by cl.id, sc.student_id
        order by c.id, cl.id;
        """
    )
    rows = db.execute(query, {"student_id": student_id, "semester": semester}).mappings()
    return [ClassProgress.model_validate(r) for r in rows]
