from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import OsceResult

router = APIRouter(prefix="/osce", tags=["osce"])


@router.get("/results", response_model=list[OsceResult])
def list_osce_results(
    student_id: int | None = None,
    semester: str | None = None,
    db: Session = Depends(get_db),
):
    query = text(
        """
        select
            r.student_id,
            e.name as exam,
            e.semester,
            e.exam_date,
            st.name as station,
            comp.name as competency,
            r.points_achieved,
            st.max_points,
            case when r.passed = 1 then 'Bestanden' else 'Nicht bestanden' end as status
        from student_osce_results as r
        join osce_stations as st on r.station_id = st.id
        join osce_exams as e on st.exam_id = e.id
        left join competencies as comp on st.competency_id = comp.id
        where (:student_id is null or r.student_id = :student_id)
          and (:semester is null or e.semester = :semester)
        order by e.exam_date, r.student_id;
        """
    )
    rows = db.execute(query, {"student_id": student_id, "semester": semester}).mappings()
    return [OsceResult.model_validate(r) for r in rows]
