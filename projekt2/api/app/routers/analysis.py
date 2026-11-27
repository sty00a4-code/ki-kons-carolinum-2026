"""KI-Analyseteil des Projekts.

Struktur: Trajektorie aus der DB bauen -> an ein LLM schicken -> Ergebnis
persistieren -> abrufbar machen. Den LLM-Client gibt die Umgebungsvariable
LLM_CLI vor (Pfad oder Name eines Kommandos im PATH), LLM_MODEL optional das
Modell. Ist LLM_CLI nicht gesetzt, liefert die Analyse den Platzhalter.

Asynchroner Vertrag: POST /analysis/jobs antwortet sofort mit 202 und einer
job_id, die Analyse läuft danach im Hintergrund, der Zustand steht in der
Tabelle analysis_jobs und wird über GET /analysis/jobs/{job_id} abgefragt
(queued -> running -> completed | failed, plus progress 0 bis 1).

Grenze: Der Hintergrundlauf nutzt FastAPI-BackgroundTasks, also den eigenen
Prozess. Der Job-STATUS überlebt einen Neustart, die laufende Arbeit nicht:
beim Start werden unfertige Jobs als failed markiert. Für echte
Ausfallsicherheit und mehrere Worker kommt später eine Task-Queue (RQ/Celery);
der HTTP-Vertrag bleibt dabei gleich.
"""

import json
import os
import subprocess
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from .. import audit, database
from ..database import get_db
from ..repositories import jobs
from ..schemas import JobCreate, JobCreated, JobOut
from ..security import User, any_user, ensure_student_access, staff
from ..services import assignment_service

router = APIRouter(prefix="/analysis", tags=["analysis"])


def build_learning_trajectory(student_id: int, db: Session) -> dict:
    """Sammelt die Rohdaten, die die KI-Analyse als Kontext braucht."""
    category_progress = (
        db.execute(
            text(
                """
            select c.name as category, sc.semester, sum(sc.points) as points,
                c.min_points as min_points
            from (
                select cl.category_id as category_id, s.semester, s.points
                from students_classes as s
                join classes as cl on s.class_id = cl.id
                where s.student_id = :student_id
                union all
                -- direkt an der Kategorie vergebene Punkte zählen mit
                select category_id, semester, points
                from students_categories
                where student_id = :student_id
            ) as sc
            join categories as c on sc.category_id = c.id
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


def run_job(job_id: str) -> None:
    """Führt einen Analyse-Job aus. Läuft im Hintergrund mit einer EIGENEN
    Session (die des Requests ist dann schon geschlossen) und schreibt Status
    und Fortschritt nach jedem Schritt, damit GET /jobs/{id} ihn sieht."""
    db = database.SessionLocal()
    try:
        job = jobs.get(db, job_id)
        if job is None:
            return
        jobs.mark_running(db, job_id)
        db.commit()
        trajectory = build_learning_trajectory(job["student_id"], db)
        jobs.set_progress(db, job_id, 0.4)
        db.commit()
        insight = call_llm_for_insights(trajectory)
        jobs.complete(db, job_id, insight)
        db.commit()
    except Exception as error:  # noqa: BLE001 - jeder Fehler wird am Job vermerkt
        db.rollback()
        jobs.fail(db, job_id, f"{type(error).__name__}: {error}")
        db.commit()
    finally:
        db.close()


def _require_student(student_id: int, db: Session) -> None:
    row = db.execute(
        text("select 1 from students where id = :id"), {"id": student_id}
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Student nicht gefunden")


@router.post("/jobs", response_model=JobCreated, status_code=202)
def create_analysis_job(
    payload: JobCreate,
    background: BackgroundTasks,
    user: User = Depends(staff),
    db: Session = Depends(get_db),
):
    """Legt einen Analyse-Job an und antwortet sofort mit 202. Den Stand holt
    man über GET /analysis/jobs/{job_id}. 404 bei unbekanntem Studenten."""
    _require_student(payload.student_id, db)
    job_id = jobs.create(db, payload.student_id, user.username)
    audit.record(
        db, user, "create", "analysis_job", job_id, after={"student_id": payload.student_id}
    )
    db.commit()
    background.add_task(run_job, job_id)
    return JobCreated(job_id=job_id)


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_analysis_job(
    job_id: str, user: User = Depends(any_user), db: Session = Depends(get_db)
):
    """Status und, sobald fertig, das Ergebnis. Studierende sehen nur Jobs,
    die sie selbst betreffen."""
    job = jobs.get(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job nicht gefunden")
    if job["student_id"] is not None:
        ensure_student_access(user, job["student_id"])
    return JobOut.model_validate(job)


@router.post("/students/{student_id}/trigger", deprecated=True)
def trigger_learning_analysis(
    student_id: int, user: User = Depends(staff), db: Session = Depends(get_db)
):
    """VERALTET, stattdessen POST /analysis/jobs. Läuft wie bisher synchron
    (Antwort erst, wenn der Job fertig ist), speichert den Job aber jetzt in
    der Datenbank. status ist wie beim neuen Vertrag completed oder failed
    (früher: done)."""
    _require_student(student_id, db)
    job_id = jobs.create(db, student_id, user.username)
    db.commit()
    run_job(job_id)
    return {"job_id": job_id, "status": jobs.get(db, job_id)["status"]}


@router.get(
    "/students/{student_id}/patient-recommendations", dependencies=[Depends(staff)]
)
def get_patient_recommendations(
    student_id: int, limit: int = 5, db: Session = Depends(get_db)
):
    """Für einen Studenten: Patienten geordnet danach, wie viel sie zu den
    offenen Anforderungen (fehlende Punkte/Fallzahl je Klasse) beitragen
    könnten. Nicht-exklusiv - mehrere Studenten können hier denselben
    Patienten empfohlen bekommen."""
    return assignment_service.rank_patients_for_student(student_id, db, limit=limit)


@router.get("/patient-matching", dependencies=[Depends(staff)])
def get_patient_matching(
    strategy: Annotated[str, Query(pattern="^(hungarian|greedy)$")] = "hungarian",
    max_per_student: Annotated[int | None, Query(ge=1, le=100)] = None,
    db: Session = Depends(get_db),
):
    """Zuordnung ALLER Patienten zu Studenten, je nach größtem Beitrag zur
    Deckung offener Anforderungen; jeder Patient geht an höchstens einen
    Studenten. strategy=hungarian (Standard): rundenweise optimal. strategy=greedy:
    früheres Verfahren, nur zum Vergleich. max_per_student begrenzt die
    Gesamtzahl je Student."""
    return assignment_service.suggest_global_matching(
        db, strategy=strategy, max_per_student=max_per_student
    )
