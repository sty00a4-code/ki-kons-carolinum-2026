"""Legt DEMO-Patientenfälle an (klar markiert, jederzeit löschbar).

    python -m scripts.seed_faelle

Die Fälle sind so gewählt, dass sie die real größten Lücken der Probanden
adressieren (Chirurgie/KFO bei allen 0 %, Prothetik-Lücke bei Stud. 4) –
damit zeigt das Matching auf Anhieb sinnvolle Empfehlungen. Vor dem echten
Betrieb löschen (Fälle-Seite → Löschen) und echte Fälle anlegen.
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.catalog import find_item
from app.db import get_db
from app.security import new_token

# (Fall-Nr., Beschreibung, Schwierigkeit, Minuten, [(code, anzahl), ...])
DEMO_CASES = [
    (
        "Fall-D01",
        "DEMO: Chirurgie-Sprechstunde (MSH-Untersuchung + OP-Planung)",
        1,
        90,
        [("chir_msh", 2), ("chir_dvt", 2)],
    ),
    (
        "Fall-D02",
        "DEMO: KFO-Fallaufnahme (Erstgespräch bis Modell)",
        1,
        120,
        [
            ("kfo_erstgespraech", 1),
            ("kfo_anamnese", 1),
            ("kfo_abformung", 1),
            ("kfo_modell", 1),
        ],
    ),
    (
        "Fall-D03",
        "DEMO: Implantat-Beratung + Nachsorge",
        1,
        60,
        [("chir_impl_beratung", 2), ("chir_impl_nachsorge", 2)],
    ),
    (
        "Fall-D04",
        "DEMO: Krone auf Zahn (inkl. Stumpfaufbau)",
        3,
        240,
        [("proth_krone", 1)],
    ),
    (
        "Fall-D05",
        "DEMO: KFO-Diagnostik (3D-Analyse, Foto, Rö, Plan)",
        2,
        150,
        [("kfo_3d", 1), ("kfo_foto", 1), ("kfo_roentgen", 1), ("kfo_plan", 1)],
    ),
]

app = create_app()
with app.app_context():
    db = get_db()
    dok = db.execute(
        "select id from users where role='doktorand' order by id limit 1"
    ).fetchone()
    created = 0
    for ref, desc, diff, minutes, items in DEMO_CASES:
        if db.execute(
            "select 1 from patient_cases where case_ref = ?", (ref,)
        ).fetchone():
            print(f"  {ref}: existiert schon – übersprungen")
            continue
        cur = db.execute(
            "insert into patient_cases (public_token, case_ref, description, difficulty, "
            "est_minutes, status, created_by, created_at) values (?,?,?,?,?,?,?,?)",
            (
                new_token(),
                ref,
                desc,
                diff,
                minutes,
                "offen",
                dok["id"] if dok else None,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        for code, cnt in items:
            it = find_item(code)
            db.execute(
                "insert into patient_case_items (case_id, item_code, item_name, category, "
                "count, points) values (?,?,?,?,?,?)",
                (
                    cur.lastrowid,
                    it["code"],
                    it["name"],
                    it["category"],
                    cnt,
                    it["points_min"] * cnt,
                ),
            )
        created += 1
        print(f"  {ref}: angelegt ({desc})")
    db.commit()
    print(f"\n{created} Demo-Fälle angelegt.")
