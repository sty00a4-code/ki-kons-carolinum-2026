"""Datenzugriff auf analysis_jobs. Zustandsautomat: queued -> running ->
completed | failed. Kein Commit hier, das macht der Aufrufer."""

import json
import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

_COLUMNS = (
    "id, student_id, status, progress, result, error, created_by, "
    "created_at, started_at, finished_at"
)


def create(db: Session, student_id: int, created_by: str) -> str:
    job_id = uuid.uuid4().hex
    db.execute(
        text(
            """
            insert into analysis_jobs (id, student_id, status, progress, created_by)
            values (:id, :student_id, 'queued', 0, :created_by)
            """
        ),
        {"id": job_id, "student_id": student_id, "created_by": created_by},
    )
    return job_id


def get(db: Session, job_id: str) -> dict | None:
    row = (
        db.execute(
            text(f"select {_COLUMNS} from analysis_jobs where id = :id"), {"id": job_id}
        )
        .mappings()
        .first()
    )
    if row is None:
        return None
    job = dict(row)
    job["job_id"] = job.pop("id")
    job["result"] = json.loads(job["result"]) if job["result"] else None
    return job


def mark_running(db: Session, job_id: str) -> None:
    db.execute(
        text(
            """
            update analysis_jobs
            set status = 'running', progress = 0.1, started_at = current_timestamp
            where id = :id
            """
        ),
        {"id": job_id},
    )


def set_progress(db: Session, job_id: str, progress: float) -> None:
    db.execute(
        text("update analysis_jobs set progress = :p where id = :id"),
        {"p": progress, "id": job_id},
    )


def complete(db: Session, job_id: str, result: dict) -> None:
    db.execute(
        text(
            """
            update analysis_jobs
            set status = 'completed', progress = 1, result = :result,
                finished_at = current_timestamp
            where id = :id
            """
        ),
        {"result": json.dumps(result, ensure_ascii=False), "id": job_id},
    )


def fail(db: Session, job_id: str, error: str) -> None:
    db.execute(
        text(
            """
            update analysis_jobs
            set status = 'failed', error = :error, finished_at = current_timestamp
            where id = :id
            """
        ),
        {"error": error[:1000], "id": job_id},
    )


def fail_orphans(db: Session) -> int:
    """Beim Start: Jobs, die in einem früheren Prozess liefen, kommen nie mehr
    zu Ende. Sie werden als fehlgeschlagen markiert statt ewig 'running' zu zeigen."""
    result = db.execute(
        text(
            """
            update analysis_jobs
            set status = 'failed', error = 'Server wurde neu gestartet',
                finished_at = current_timestamp
            where status in ('queued', 'running')
            """
        )
    )
    return result.rowcount
