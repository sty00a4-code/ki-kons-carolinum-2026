"""Gerüst für den KI-Analyseteil des Projekts.

Aktuell ein synchroner Platzhalter (kein echter LLM-Call), aber mit der
Struktur, die für den echten Aufruf gebraucht wird: Trajektorie aus der DB
bauen -> an ein LLM schicken -> Ergebnis persistieren -> abrufbar machen.
Sobald ihr die LLM-API angebunden habt, nur `call_llm_for_insights` ersetzen.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import assignment_service

router = APIRouter(prefix="/analysis", tags=["analysis"])

# Platzhalter-Speicher für Job-Status. Für den Uni-Server durch eine echte
# Tabelle (z.B. analysis_jobs) oder einen Task-Queue-Status (Celery/RQ) ersetzen.
_JOBS: dict[str, dict] = {}


def build_learning_trajectory(student_id: int, db: Session) -> dict:
    """Sammelt die Rohdaten, die die KI-Analyse als Kontext braucht."""
    category_progress = (
        db.execute(
            text(
                """
            select c.name as category, sc.semester, sum(sc.points) as points
            from students_classes as sc
            join classes as cl on sc.class_id = cl.id
            join categories as c on cl.category_id = c.id
            where sc.student_id = :student_id
            group by c.id, sc.semester
            order by sc.semester, c.id;
            """
            ),
            {"student_id": student_id},
        )
        .mappings()
        .all()
    )

    return {
        "student_id": student_id,
        "category_progress": [dict(r) for r in category_progress],
    }


def call_llm_for_insights(trajectory: dict) -> dict:
    """TODO: hier den echten LLM-API-Call einbauen (siehe outline: 'Nutzung
    von zentral angebotenen LLMs per API'). Platzhalter gibt Rohdaten zurück."""
    return {
        "student_id": trajectory["student_id"],
        "summary": "Platzhalter: LLM-Anbindung noch nicht implementiert.",
        "raw_context_size": len(trajectory["category_progress"]),
    }


@router.post("/students/{student_id}/trigger")
def trigger_learning_analysis(student_id: int, db: Session = Depends(get_db)):
    trajectory = build_learning_trajectory(student_id, db)
    insight = call_llm_for_insights(trajectory)

    job_id = str(uuid.uuid4())
    _JOBS[job_id] = {"status": "done", "student_id": student_id, "result": insight}
    return {"job_id": job_id, "status": "done"}


@router.get("/jobs/{job_id}")
def get_analysis_status(job_id: str):
    job = _JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job nicht gefunden")
    return job


@router.get("/students/{student_id}/patient-recommendations")
def get_patient_recommendations(
    student_id: int, limit: int = 5, db: Session = Depends(get_db)
):
    """Für einen Studenten: Patienten geordnet danach, wie viel sie zu den
    offenen Anforderungen (fehlende Punkte/Fallzahl je Klasse) beitragen
    könnten. Nicht-exklusiv - mehrere Studenten können hier denselben
    Patienten empfohlen bekommen."""
    return assignment_service.rank_patients_for_student(student_id, db, limit=limit)


@router.get("/patient-matching")
def get_patient_matching(db: Session = Depends(get_db)):
    """Zuordnung ALLER Patienten zu Studenten: jeder Patient wird höchstens
    einem Studenten zugewiesen, gewählt danach, wo er den größten Beitrag zur
    Deckung offener Anforderungen leistet (greedy, nicht global optimal)."""
    return assignment_service.suggest_global_matching(db)
