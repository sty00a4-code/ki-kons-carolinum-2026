from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..pagination import Page, fetch_page, page_params
from ..schemas import (
    CategoryPointsOut,
    CategoryPointsValue,
    CategoryProgress,
    ClassProgress,
    StudentOut,
    StudentOverview,
)
from ..security import (
    User,
    any_user,
    ensure_student_access,
    require_roles,
    scoped_student_id,
)
from ..semester import SEMESTER_PATTERN
from .categories import remove_category_points, upsert_category_points

router = APIRouter(prefix="/students", tags=["students"])

# Filter ?semester= wird wie im Body geprüft (422 bei falschem Format).
SemesterFilter = Annotated[str | None, Query(pattern=SEMESTER_PATTERN)]
SemesterPath = Annotated[str, Path(pattern=SEMESTER_PATTERN)]


@router.get("", response_model=list[StudentOut])
def list_students(
    response: Response,
    page: Page = Depends(page_params),
    user: User = Depends(any_user),
    db: Session = Depends(get_db),
):
    """Studierende sehen nur sich selbst, Lehrende und Admins alle."""
    only = scoped_student_id(user, None)
    rows = fetch_page(
        db,
        response,
        """
        select id, anon_code, enrollment_semester from students
        where (:only is null or id = :only)
        order by id
        """,
        {"only": only},
        page,
    )
    return [StudentOut.model_validate(r) for r in rows]


@router.get("/{student_id}/category-progress", response_model=list[CategoryProgress])
def get_category_progress(
    student_id: int,
    semester: SemesterFilter = None,
    user: User = Depends(any_user),
    db: Session = Depends(get_db),
):
    ensure_student_access(user, student_id)
    return _category_progress(student_id, semester, db)


def _category_progress(
    student_id: int, semester: str | None, db: Session
) -> list[CategoryProgress]:
    """Fortschritt pro Kategorie: total_points = students_classes (über die
    Klassen) PLUS students_categories (direkt an der Kategorie vergeben, s.
    routers/categories.py). Eine Kategorie zählt auch, wenn nur eine der
    beiden Quellen Einträge hat."""
    # per_class/per_category getrennt aggregiert, nicht direkt gejoint - ein
    # Join über category_id würde die Zeilen der einen Seite mit denen der
    # anderen multiplizieren und die Summen verfälschen.
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
            coalesce(pcl.pts, 0) as class_points,
            coalesce(pca.pts, 0) as direct_points,
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
def get_direct_category_points(
    student_id: int,
    user: User = Depends(any_user),
    db: Session = Depends(get_db),
):
    """Nur die DIREKT an Kategorien vergebenen Punkte dieses Studenten
    (students_categories), ohne die über Klassen erreichten - zur Kontrolle,
    was pauschal statt über eine Unterkategorie eingetragen wurde."""
    ensure_student_access(user, student_id)
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


@router.put(
    "/{student_id}/categories/{category_id}/points/{semester}",
    response_model=CategoryPointsOut,
)
def put_category_points(
    student_id: int,
    category_id: int,
    semester: SemesterPath,
    payload: CategoryPointsValue,
    user: User = Depends(require_roles("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """Setzt die direkt vergebenen Punkte (Upsert, ersetzt, addiert nicht).
    Student, Kategorie und Semester bilden zusammen die Identität der Ressource
    und stehen deshalb alle in der URL. 404 bei unbekanntem Studenten oder
    unbekannter Kategorie."""
    return upsert_category_points(
        db, user, student_id, category_id, semester, payload.points,
        missing_student_status=404,
    )


@router.delete(
    "/{student_id}/categories/{category_id}/points/{semester}", status_code=204
)
def delete_category_points_for_student(
    student_id: int,
    category_id: int,
    semester: SemesterPath,
    user: User = Depends(require_roles("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """Nimmt direkt vergebene Punkte zurück. 404, wenn es den Eintrag nicht gibt."""
    remove_category_points(db, user, student_id, category_id, semester)
    return Response(status_code=204)


@router.get("/{student_id}/class-progress", response_model=list[ClassProgress])
def get_class_progress(
    student_id: int,
    semester: SemesterFilter = None,
    user: User = Depends(any_user),
    db: Session = Depends(get_db),
):
    ensure_student_access(user, student_id)
    return _class_progress(student_id, semester, db)


def _class_progress(
    student_id: int, semester: str | None, db: Session
) -> list[ClassProgress]:
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


@router.get(
    "/{student_id}/overview", response_model=StudentOverview, tags=["read-models"]
)
def get_student_overview(
    student_id: int,
    user: User = Depends(any_user),
    db: Session = Depends(get_db),
):
    """READ MODEL für die UI, keine kanonische Ressource: eine auf die
    Darstellung zugeschnittene Aggregation aus Kategorie-Fortschritt (inkl.
    direkt vergebener Punkte), erfüllten/offenen Kategorien und Klassen, Zahl
    der Behandlungen und zugeordneten Patienten. Die maßgeblichen Daten liegen
    unter /students/{id}/category-progress, /class-progress usw.
    404 bei unbekannter student_id."""
    ensure_student_access(user, student_id)
    student = (
        db.execute(
            text(
                "select id, anon_code, enrollment_semester from students where id = :id"
            ),
            {"id": student_id},
        )
        .mappings()
        .first()
    )
    if student is None:
        raise HTTPException(status_code=404, detail="Student nicht gefunden")

    categories = _category_progress(student_id, None, db)
    classes = _class_progress(student_id, None, db)
    treatment_count = db.execute(
        text(
            "select count(*) from treatment_cases "
            "where student_id = :id and deleted_at is null"
        ),
        {"id": student_id},
    ).scalar()
    assigned = (
        db.execute(
            text(
                """
            select coalesce(p.pseudonym, p.name) as patient
            from patient_assignments as pa
            join patients as p on pa.patient_id = p.id
            where pa.student_id = :id
            order by p.id
            """
            ),
            {"id": student_id},
        )
        .scalars()
        .all()
    )

    categories_done = sum(1 for c in categories if c.done)
    classes_done = sum(1 for c in classes if c.done)
    return StudentOverview(
        student=StudentOut.model_validate(student),
        category_progress=categories,
        categories_done=categories_done,
        categories_open=len(categories) - categories_done,
        classes_done=classes_done,
        classes_open=len(classes) - classes_done,
        treatment_count=treatment_count,
        assigned_patients=list(assigned),
    )
