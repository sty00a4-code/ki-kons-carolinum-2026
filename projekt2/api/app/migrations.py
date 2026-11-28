"""Versionierte Schema-Migrationen für die SQLite-Datenbank.

Ersetzt das frühere ensure_schema(): Statt bei jedem Start implizit das Schema
zu verändern, gibt es nummerierte Schritte, die in der Tabelle
schema_migrations verbucht werden.

    python -m app.cli migrate      # ausstehende Schritte anwenden
    python -m app.cli status       # Stand anzeigen

Betrieb: In der Entwicklung wendet die API beim Start ausstehende Schritte
selbst an (PROJEKT2_AUTO_MIGRATE, Standard an). In Produktion ist das aus:
erst migrieren, dann die API starten. Startet sie mit offenen Migrationen,
bricht sie ab, statt das Schema zu verändern oder mit altem Schema zu laufen.

Jeder Schritt ist idempotent (prüft, bevor er anlegt). SQLite macht DDL nicht
transaktional; bricht ein Schritt mittendrin ab, ist er nach dem Beheben
einfach erneut ausführbar. Neue Schritte werden unten an MIGRATIONS angehängt,
bestehende nie verändert.

Hinweis zu Alembic: für den geplanten Umstieg auf PostgreSQL ist Alembic die
richtige Wahl. Diese Schritte nutzen SQLite-Syntax (pragma, autoincrement) und
müssten dafür neu geschrieben werden.
"""

from collections.abc import Callable
from dataclasses import dataclass


def _run(conn, sql: str) -> list:
    """Führt SQL auf einer SQLAlchemy-Connection oder einer sqlite3-Connection aus."""
    if hasattr(conn, "exec_driver_sql"):
        result = conn.exec_driver_sql(sql)
        return list(result.fetchall()) if result.returns_rows else []
    return conn.execute(sql).fetchall()


def _columns(conn, table: str) -> set[str]:
    return {row[1] for row in _run(conn, f"pragma table_info({table})")}


def _add_columns(conn, specs: list[tuple[str, str, str]]) -> None:
    for table, column, definition in specs:
        if column not in _columns(conn, table):
            _run(conn, f"alter table {table} add column {column} {definition}")


def _statements(conn, statements: list[str]) -> None:
    for statement in statements:
        _run(conn, statement)


# --- 1: Stand des früheren ensure_schema() -------------------------------------------


def _m1_baseline(conn) -> None:
    _add_columns(
        conn,
        [
            ("classes", "stretchable", "integer default 1"),
            ("classes", "max_semesters", "integer"),
            ("patients", "pseudonym", "varchar(50)"),
            ("patients", "age", "integer"),
            ("patients", "category", "integer"),
            ("patient_cases", "difficulty", "integer"),
            ("patient_cases", "expected_dur_min", "integer"),
            ("treatment_cases", "patient_case_id", "int references patient_cases (id)"),
        ],
    )
    _statements(
        conn,
        [
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
            """
            create table if not exists students_categories (
                student_id int references students (id),
                category_id int references categories (id),
                semester varchar(8),
                points decimal default 0,
                primary key (student_id, category_id, semester)
            )
            """,
        ],
    )


# --- 2: Benutzer und Audit-Log ------------------------------------------------------


def _m2_users_and_audit(conn) -> None:
    _statements(
        conn,
        [
            """
            create table if not exists users (
                id integer primary key autoincrement,
                username varchar(100) not null unique,
                password_hash text not null,
                role varchar(20) not null
                    check (role in ('student', 'teacher', 'admin')),
                student_id int references students (id),
                active integer not null default 1,
                created_at text default current_timestamp,
                last_login_at text
            )
            """,
            """
            create table if not exists audit_log (
                id integer primary key autoincrement,
                ts text not null default current_timestamp,
                user_id int,
                username varchar(100),
                role varchar(20),
                action varchar(20) not null,
                entity varchar(50) not null,
                entity_id text,
                before_json text,
                after_json text,
                reason text
            )
            """,
            "create index if not exists idx_audit_log_entity on audit_log (entity, entity_id)",
            "create index if not exists idx_audit_log_ts on audit_log (ts)",
        ],
    )


# --- 3: Soft Delete für Behandlungen, Zuordnungs-Historie ----------------------------


def _m3_history_and_soft_delete(conn) -> None:
    _add_columns(
        conn,
        [
            ("treatment_cases", "deleted_at", "text"),
            ("treatment_cases", "deleted_by", "varchar(100)"),
            ("treatment_cases", "deletion_reason", "text"),
            # sqlite erlaubt bei add column keinen current_timestamp-Default;
            # null heißt daher "noch nie geändert", gelesen wird coalesce(updated_at, created_at).
            ("patient_assignments", "updated_at", "text"),
        ],
    )
    _statements(
        conn,
        [
            """
            create table if not exists patient_assignment_history (
                id integer primary key autoincrement,
                patient_id int not null,
                student_id int,
                semester varchar(8),
                note text,
                valid_from text,
                valid_to text default current_timestamp,
                change varchar(20) not null,
                changed_by varchar(100)
            )
            """,
            "create index if not exists idx_assignment_history_patient "
            "on patient_assignment_history (patient_id)",
            "create index if not exists idx_treatment_cases_patient_case "
            "on treatment_cases (patient_case_id)",
        ],
    )


# --- 4: persistente Analyse-Jobs -----------------------------------------------------


def _m4_analysis_jobs(conn) -> None:
    _statements(
        conn,
        [
            """
            create table if not exists analysis_jobs (
                id text primary key,
                student_id int references students (id),
                status varchar(20) not null,
                progress real not null default 0,
                result text,
                error text,
                created_by varchar(100),
                created_at text default current_timestamp,
                started_at text,
                finished_at text
            )
            """,
            "create index if not exists idx_analysis_jobs_student "
            "on analysis_jobs (student_id)",
        ],
    )


def _m5_unique_student_login(conn) -> None:
    # Ein Student hat höchstens ein Konto. Schlägt fehl, wenn schon Duplikate
    # existieren: dann erst die überzähligen Konten sperren/löschen.
    _statements(
        conn,
        [
            "create unique index if not exists idx_users_student_id "
            "on users (student_id) where student_id is not null"
        ],
    )


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    apply: Callable


MIGRATIONS: list[Migration] = [
    Migration(1, "baseline (früheres ensure_schema)", _m1_baseline),
    Migration(2, "users und audit_log", _m2_users_and_audit),
    Migration(3, "soft delete und Zuordnungs-Historie", _m3_history_and_soft_delete),
    Migration(4, "analysis_jobs", _m4_analysis_jobs),
    Migration(5, "eindeutige student_id je Benutzer", _m5_unique_student_login),
]


def _applied_versions(conn) -> set[int]:
    exists = _run(
        conn,
        "select 1 from sqlite_master where type = 'table' and name = 'schema_migrations'",
    )
    if not exists:
        return set()
    return {row[0] for row in _run(conn, "select version from schema_migrations")}


def _pending(conn) -> list[Migration]:
    done = _applied_versions(conn)
    return [m for m in MIGRATIONS if m.version not in done]


def apply_migrations(conn) -> list[Migration]:
    """Wendet alle ausstehenden Schritte der Reihe nach an und gibt sie zurück."""
    _run(
        conn,
        """
        create table if not exists schema_migrations (
            version integer primary key,
            name text not null,
            applied_at text default current_timestamp
        )
        """,
    )
    applied = []
    for migration in _pending(conn):
        migration.apply(conn)
        escaped = migration.name.replace("'", "''")
        _run(
            conn,
            f"insert into schema_migrations (version, name) "
            f"values ({migration.version}, '{escaped}')",
        )
        applied.append(migration)
    return applied


def migrate(engine) -> list[Migration]:
    with engine.begin() as conn:
        return apply_migrations(conn)


def pending_migrations(engine) -> list[Migration]:
    with engine.connect() as conn:
        return _pending(conn)


def current_version(engine) -> int:
    with engine.connect() as conn:
        done = _applied_versions(conn)
    return max(done) if done else 0
