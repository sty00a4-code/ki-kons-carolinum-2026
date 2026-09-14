from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import PatientCase

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/{patient_id}/cases", response_model=list[PatientCase])
def get_patient_cases(patient_id: int, db: Session = Depends(get_db)):
    query = text(
        """
        select
            p.id as patient_id,
            p.name as patient,
            c.name as category,
            cl.name as class_name,
            pc.region,
            pc.min_points,
            pc.max_points
        from patient_cases as pc
        join patients as p on pc.patient_id = p.id
        join classes as cl on pc.class_id = cl.id
        join categories as c on cl.category_id = c.id
        where p.id = :patient_id
        order by c.id, cl.id;
        """
    )
    rows = db.execute(query, {"patient_id": patient_id}).mappings()
    return [PatientCase.model_validate(r) for r in rows]
