"""Legt die Datenbank neu an – mit Demo-Zugängen und realistischen Beispiel-Daten.

    python -m scripts.init_db

Was passiert:
- 1 Doktorand (Prüfer "Dr. Sabine Wagner") + 5 Studierende mit Klarnamen.
- Studierende loggen sich mit ihrer pseudonymen Kennung ein (nicht erratbar);
  der Doktorand sieht überall die Klarnamen.
- Jede/r Studierende bekommt ein realistisches Leistungsprofil über die vier
  Semester IK I–IV (WiSe 2024/25 bis SoSe 2026) – dadurch zeigen die
  Auswertungs-Grafiken (Vergleich, Matrix, Verlauf) echte Unterschiede.
- Alle Pflichtfelder sind gefüllt (Datum, Fallbezug, Schwierigkeit, Zeit, Notiz).

ACHTUNG: löscht bestehende Tabellen (nur für Demo/Setup).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import generate_password_hash

from app import create_app
from app.catalog import CATALOG, CATEGORY_TARGET, SEMESTERS, find_item
from app.db import get_db, init_db
from app.security import new_token

# Klarname + Zielprofil (Anteil der Mindestanforderung, der schon erreicht ist)
STUDENTS = [
    ("Anna Berg", 0.82),
    ("Ben Klein", 0.51),
    ("Carla Ott", 0.34),
    ("David Sun", 0.66),
    ("Eva Roth", 0.18),
]

# Repräsentatives Datum je Semester (IK I = WiSe 2024/25 … IK IV = SoSe 2026)
SEM_DATE = {
    "IK I": "2024-11-15",
    "IK II": "2025-05-20",
    "IK III": "2025-11-18",
    "IK IV": "2026-05-12",
}

NOTES = {
    "Parodontologie": "PA-Behandlung dokumentiert",
    "Zahnhartsubstanz/Prävention/Restauration": "Restaurative Versorgung",
    "Endodontologie": "Endodontische Behandlung",
    "Kinderzahnheilkunde": "Kinderbehandlung",
    "Prothetik": "Prothetische Versorgung",
    "Schnittmenge Restauration/Prothetik": "Restaurativ-prothetisch",
    "Chirurgie/Implantologie": "Chirurgische Leistung",
    "Kieferorthopädie (KFO)": "KFO-Behandlungsschritt",
}


def build_entries(profile):
    """Erzeugt genehmigte Einträge, bis je Kategorie ~profile*Soll erreicht ist.

    Frühe Punkte landen in IK I, spätere in IK II–IV -> realistischer Verlauf.
    """
    entries = []
    for category, items in CATALOG:
        goal = CATEGORY_TARGET.get(category, 0) * profile
        if goal <= 0:
            continue
        acc, i = 0.0, 0
        while acc < goal and i < 60:
            it = items[i % len(items)]
            pts = it["points_min"]
            # Anzahl so wählen, dass das Kategorie-Ziel nicht stark überschossen
            # wird (sonst hätten alle Profile denselben Kategorien-Wert).
            remaining = goal - acc
            cnt = max(1, min(int(it["soll_anzahl"]), int(-(-remaining // pts))))
            frac = acc / goal
            sem = SEMESTERS[min(3, int(frac * 4))]
            entries.append(
                {
                    "code": it["code"],
                    "sem": sem,
                    "count": cnt,
                    "points": pts,
                    "difficulty": (i % 3) + 1,
                    "time_minutes": int(pts * 45 * cnt),
                    "note": NOTES.get(category, ""),
                }
            )
            acc += pts * cnt
            i += 1
    return entries


app = create_app()
with app.app_context():
    init_db()
    db = get_db()

    cur = db.execute(
        "insert into users (username, password_hash, role, real_name) values (?,?,?,?)",
        (
            "doktorand1",
            generate_password_hash("doktorand1"),
            "doktorand",
            "Dr. Sabine Wagner",
        ),
    )
    dok_id = cur.lastrowid

    def insert_perf(sid, e, status, comment=None):
        it = find_item(e["code"])
        date = SEM_DATE[e["sem"]]
        submitted = (
            date + "T10:00:00"
            if status in ("submitted", "approved", "rejected")
            else None
        )
        reviewed_by = dok_id if status in ("approved", "rejected") else None
        reviewed_at = date + "T15:00:00" if reviewed_by else None
        if status == "approved" and comment is None:
            comment = "Geprüft – in Ordnung."
        db.execute(
            "insert into performances (public_token, student_id, semester, category, "
            "item_code, item_name, count, points, patient_ref, performed_on, difficulty, "
            "time_minutes, note, status, created_at, submitted_at, reviewed_by, "
            "reviewed_at, review_comment) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                new_token(),
                sid,
                e["sem"],
                it["category"],
                it["code"],
                it["name"],
                e["count"],
                e["points"],
                "Fall-" + new_token(2),
                date,
                e.get("difficulty", 2),
                e.get("time_minutes", int(e["points"] * 45)),
                e.get("note", ""),
                status,
                date + "T09:00:00",
                submitted,
                reviewed_by,
                reviewed_at,
                comment,
            ),
        )

    print("== DEMO-Zugänge (Passwort = Benutzername) ==")
    print("Doktorand:  doktorand1 / doktorand1   (Dr. Sabine Wagner)\n")
    print("Studierende (Login = Kennung, Passwort = dieselbe Kennung):")
    for idx, (name, profile) in enumerate(STUDENTS):
        pseudonym = "S-" + new_token(4)
        cur = db.execute(
            "insert into students (pseudonym, real_name, cohort) values (?,?,?)",
            (pseudonym, name, "IK-Kohorte 2024–2026"),
        )
        sid = cur.lastrowid
        db.execute(
            "insert into users (username, password_hash, role, student_id) values (?,?,?,?)",
            (pseudonym, generate_password_hash(pseudonym), "student", sid),
        )
        n = 0
        for e in build_entries(profile):
            insert_perf(sid, e, "approved")
            n += 1
        print(
            f"  {pseudonym}   {name}  (~{int(profile * 100)} % Fortschritt, {n} Einträge)"
        )

    db.commit()
    print("\nDatenbank angelegt:", app.config["DATABASE"])
    print("doktorand1 -> 'Auswertung': Vergleich aller Studierenden + Kompetenzmatrix.")
    print(
        "'Entwicklung ansehen' pro Studierendem: Verlauf über die Jahre + Radar + Fortschritt."
    )
