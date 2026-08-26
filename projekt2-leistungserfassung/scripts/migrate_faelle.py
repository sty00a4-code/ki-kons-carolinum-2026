"""Migration: Patientenfall-Tabellen zur BESTEHENDEN Datenbank hinzufügen.

    python -m scripts.migrate_faelle

Legt patient_cases + patient_case_items an, OHNE vorhandene Daten
(Studierende, Leistungen, Logins) anzufassen – anders als init_db /
import_probanden, die die Datenbank neu aufbauen.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.db import get_db

DDL = """
create table if not exists patient_cases (
    id            integer primary key autoincrement,
    public_token  text unique not null,
    case_ref      text unique not null,
    description   text,
    difficulty    integer,
    est_minutes   integer,
    status        text not null default 'offen'
                    check (status in ('offen','zugewiesen','abgeschlossen')),
    assigned_student_id integer references students(id),
    created_by    integer references users(id),
    created_at    text
);
create table if not exists patient_case_items (
    id         integer primary key autoincrement,
    case_id    integer not null references patient_cases(id),
    item_code  text not null,
    item_name  text not null,
    category   text not null,
    count      integer not null default 1,
    points     real not null
);
create index if not exists idx_case_items_case on patient_case_items(case_id);
"""

app = create_app()
with app.app_context():
    db = get_db()
    db.executescript(DDL)
    db.commit()
    n = db.execute("select count(*) from patient_cases").fetchone()[0]
    print(f"Migration ok – Tabellen vorhanden, {n} Fälle in der Datenbank.")
