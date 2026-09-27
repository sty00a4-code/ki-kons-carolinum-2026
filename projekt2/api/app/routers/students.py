from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import CategoryPointsOut, CategoryProgress, ClassProgress, StudentOut

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=list[StudentOut])
def list_students(db: Session = Depends(get_db)):
    rows = db.execute(
        text("select id, anon_code, enrollment_semester from students order by id")
    ).mappings()
    return [StudentOut.model_validate(r) for r in rows]


@router.get("/{student_id}/category-progress", response_model=list[CategoryProgress])
def get_category_progress(
    student_id: int,
    semester: str | None = None,
    db: Session = Depends(get_db),
):
    """Fortschritt pro Kategorie für einen Studenten.

    total_points ist die Summe aus zwei unabhängigen Quellen: den Punkten aus
    students_classes (über die Klassen/Unterkategorien) UND den Punkten aus
    students_categories (direkt an der Kategorie vergeben, siehe
    routers/categories.py). Eine Kategorie mit ausschließlich direkt
    vergebenen Punkten - ganz ohne Klassen-Einträge - taucht hier genauso auf
    wie eine, die nur über Klassen befüllt ist.
    """
    # Zwei getrennte Aggregate (per_class, per_category) statt eines direkten
    # Joins beider Tabellen: ein Join von students_classes und
    # students_categories über category_id würde die Zeilen der einen Seite
    # mit denen der anderen multiplizieren (Kreuzprodukt) und die Summen
    # verfälschen.
    #
    # Ohne Semester-Filter summiert die Query über alle Semester. Das Feld
    # semester liefert deshalb den Filterwert oder null und nicht einen
    # beliebigen Wert aus der Gruppe.
    query = text(
        """
        with per_class as (
            select cl.category_id as category_id, sum(sc.points) as pts
            from students_classes as sc
            join classes as cl on sc.class_id = cl.id
            where sc.student_id = :student_id
              and (:semester is null or sc.semester = :semester)
            group by cl.category_id
        ),
        per_category as (
            select sca.category_id as category_id, sum(sca.points) as pts
            from students_categories as sca
            where sca.student_id = :student_id
              and (:semester is null or sca.semester = :semester)
            group by sca.category_id
        )
        select
            c.name as category,
            :student_id as student_id,
            :semester as semester,
            coalesce(pcl.pts, 0) + coalesce(pca.pts, 0) as total_points,
            c.min_points as min,
            (coalesce(pcl.pts, 0) + coalesce(pca.pts, 0)) >= c.min_points as done,
            case
                when c.min_points > 0 then
                    100.0 * cast(coalesce(pcl.pts, 0) + coalesce(pca.pts, 0) as real) / c.min_points
                else null
            end as progress_pct
        from categories as c
        left join per_class as pcl on pcl.category_id = c.id
        left join per_category as pca on pca.category_id = c.id
        where pcl.category_id is not null or pca.category_id is not null
        order by c.id;
        """
    )
    rows = db.execute(
        query, {"student_id": student_id, "semester": semester}
    ).mappings()
    return [CategoryProgress.model_validate(r) for r in rows]


@router.get("/{student_id}/category-points", response_model=list[CategoryPointsOut])
def get_direct_category_points(student_id: int, db: Session = Depends(get_db)):
    """Nur die DIREKT an Kategorien vergebenen Punkte dieses Studenten
    (students_categories), ohne die über Klassen erreichten - zur Kontrolle,
    was pauschal statt über eine Unterkategorie eingetragen wurde."""
    rows = db.execute(
        text(
            """
            select
                sca.student_id,
                sca.category_id,
                c.name as category,
                sca.semester,
                sca.points
            from students_categories as sca
            join categories as c on sca.category_id = c.id
            where sca.student_id = :student_id
            order by c.id, sca.semester
            """
        ),
        {"student_id": student_id},
    ).mappings()
    return [CategoryPointsOut.model_validate(r) for r in rows]


@router.get("/{student_id}/class-progress", response_model=list[ClassProgress])
def get_class_progress(
    student_id: int,
    semester: str | None = None,
    db: Session = Depends(get_db),
):
    """Feingranulare Sicht: Fortschritt pro einzelner Klasse."""
    # Semester als Bind-Wert, gleicher Grund wie beim Kategorie-Fortschritt.
    query = text(
        """
        select
            c.name as category,
            cl.name as class_name,
            sc.student_id,
            :semester as semester,
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
    rows = db.execute(
        query, {"student_id": student_id, "semester": semester}
    ).mappings()
    return [ClassProgress.model_validate(r) for r in rows]
