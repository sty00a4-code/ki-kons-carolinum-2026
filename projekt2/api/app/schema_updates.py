"""Ergänzt eine bestehende leistungen.db um die Spalten und Tabellen der
Patientenplanung, ohne vorhandene Daten anzufassen.

sqlite kennt kein "add column if not exists". Deshalb liest ensure_schema
pragma table_info und legt nur an, was fehlt. Frische Datenbanken bekommen
dieselben Definitionen über leistungen.sql (build-db.py); beide Stellen
müssen zusammenpassen.
"""

from sqlalchemy import text
from sqlalchemy.engine import Engine

# Tabelle, Spalte, Definition wie in leistungen.sql. Wertebereiche (1 bis 3,
# 1 bis 4) prüft Pydantic mit 422, nicht die Datenbank.
_COLUMNS = [
    ("classes", "stretchable", "integer default 1"),
    ("classes", "max_semesters", "integer"),
    ("patients", "pseudonym", "varchar(50)"),
    ("patients", "age", "integer"),
    ("patients", "category", "integer"),
    ("patient_cases", "difficulty", "integer"),
    ("patient_cases", "expected_dur_min", "integer"),
]

_STATEMENTS = [
    """
    create table if not exists patient_assignments (
        id integer primary key autoincrement,
        patient_id int references patients (id) unique,
        student_id int references students (id),
        semester varchar(8),
        note text,
        created_at text default current_timestamp
    )
    """,
    "create unique index if not exists idx_patients_pseudonym on patients (pseudonym)",
]


def _existing_columns(connection, table: str) -> set[str]:
    rows = connection.execute(text(f"pragma table_info({table})")).mappings()
    return {r["name"] for r in rows}


def ensure_schema(engine: Engine) -> None:
    """Legt fehlende Spalten, die Tabelle patient_assignments und den Index auf
    patients.pseudonym an. Mehrfacher Aufruf ist unschädlich."""
    with engine.begin() as connection:
        for table, column, definition in _COLUMNS:
            if column in _existing_columns(connection, table):
                continue
            connection.execute(
                text(f"alter table {table} add column {column} {definition}")
            )
        for statement in _STATEMENTS:
            connection.execute(text(statement))
