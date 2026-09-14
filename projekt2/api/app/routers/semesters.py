from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db

router = APIRouter(prefix="/semesters", tags=["semesters"])


@router.get("", response_model=list[str])
def list_semesters(db: Session = Depends(get_db)):
    """Alle Semester, in denen Daten existieren. Das Format JJJJSoSe/JJJJWiSe
    sortiert lexikographisch gleich chronologisch (SoSe vor WiSe im selben Jahr)."""
    query = text(
        """
        select distinct semester from students_classes where semester is not null
        union
        select distinct semester from treatment_cases where semester is not null
        union
        select distinct semester from osce_exams where semester is not null
        order by semester;
        """
    )
    return [r["semester"] for r in db.execute(query).mappings()]
