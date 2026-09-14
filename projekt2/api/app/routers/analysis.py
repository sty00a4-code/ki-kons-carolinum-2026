"""KI-Analyseteil des Projekts.

Struktur: Trajektorie aus der DB bauen -> an ein LLM schicken -> Ergebnis
persistieren -> abrufbar machen. Den LLM-Client gibt die Umgebungsvariable
LLM_CLI vor (Pfad oder Name eines Kommandos im PATH), LLM_MODEL optional das
Modell. Ist LLM_CLI nicht gesetzt, liefert die Analyse den Platzhalter. Der
Trigger ist synchron und dauert mit LLM-Client 10 bis 30 Sekunden.
"""

import json
import os
import subprocess
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
            select c.name as category, sc.semester, sum(sc.points) as points,
                c.min_points as min_points
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
    """Ruft das Sprachmodell-Kommando aus LLM_CLI auf. Ohne die Variable oder
    bei einem Fehler kommt der Platzhalter zurück, das Feld source sagt, was
    es war."""
    fallback = {
        "student_id": trajectory["student_id"],
        "summary": "Platzhalter: LLM-Anbindung noch nicht implementiert.",
        "raw_context_size": len(trajectory["category_progress"]),
        "source": "placeholder",
    }
    command = os.environ.get("LLM_CLI")
    if not command:
        return fallback

    prompt = (
        "Du bist Betreuer im zahnmedizinischen Behandlungskurs. Die folgenden "
        "Daten sind die Punktestände eines Studierenden je Kategorie und "
        "Semester samt Mindestpunkten (min_points, Gesamtziel über alle "
        "Semester):\n"
        + json.dumps(trajectory, ensure_ascii=False)
        + "\nNenne in höchstens 120 Wörtern auf Deutsch: (1) Stärken, "
        "(2) Lücken mit Blick auf die Mindestpunkte, (3) eine konkrete "
        "Empfehlung für das kommende Semester. Keine Anrede, keine "
        "Einleitung, keine Aufzählungszeichen."
    )
    args = [command, "-p", prompt]
    model = os.environ.get("LLM_MODEL")
    if model:
        args += ["--model", model]
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return fallback
    if result.returncode != 0 or not result.stdout.strip():
        return fallback

    return {
        "student_id": trajectory["student_id"],
        "summary": result.stdout.strip(),
        "raw_context_size": len(trajectory["category_progress"]),
        "source": "llm",
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
