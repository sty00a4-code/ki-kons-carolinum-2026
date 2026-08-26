"""Exportiert die Probanden-Daten KI-tauglich (Projektplan Phase 3, UNIFR-2).

    python -m scripts.export_ki

Schreibt docs/ki-analyse/probanden_export.json:
- Metadaten (Quelle, Regeln, bekannte Lücken)
- kompletter Leistungskatalog (Blaue Liste) inkl. Soll-Werten
- je Proband die Leistungen chronologisch je Semester (IK I–III)
- Kategorien-Summen als Kontrollwerte

Datenschutz: ausschließlich Pseudonyme ("Stud. 1"–"Stud. 5"), keine
Patientendaten (Quelle enthält keine Fallbezüge).
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.catalog import CATALOG, CATEGORY_TARGET, SEMESTERS, TOTAL_TARGET
from app.db import get_db

OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "docs",
    "ki-analyse",
    "probanden_export.json",
)

app = create_app()
with app.app_context():
    db = get_db()
    katalog = []
    for category, items in CATALOG:
        katalog.append(
            {
                "kategorie": category,
                "mindestpunkte": CATEGORY_TARGET.get(category, 0),
                "leistungen": [
                    {
                        "code": it["code"],
                        "name": it["name"],
                        "punkte_min": it["points_min"],
                        "punkte_max": it["points_max"],
                        "soll_anzahl": it["soll_anzahl"],
                        "einheit": it["unit"],
                    }
                    for it in items
                ],
            }
        )

    probanden = []
    for s in db.execute("select * from students order by id").fetchall():
        sems = {}
        for r in db.execute(
            "select * from performances where student_id=? and status='approved' "
            "order by semester, category, item_code",
            (s["id"],),
        ).fetchall():
            entry = {
                "code": r["item_code"],
                "leistung": r["item_name"],
                "kategorie": r["category"],
                "punkte_summe": r["points"],
                "schwierigkeit_demo": r["difficulty"],
                "zeit_min_demo": r["time_minutes"],
            }
            if "Blocksumme" in (r["note"] or ""):
                entry["hinweis"] = (
                    "Nicht aufgeschlüsselte Blocksumme aus dem "
                    "Kursblatt – Leistungsart innerhalb des Blocks unbekannt"
                )
            sems.setdefault(r["semester"], []).append(entry)
        kat_sum = {}
        for r in db.execute(
            "select category, semester, sum(points*count) as p from performances "
            "where student_id=? and status='approved' group by category, semester",
            (s["id"],),
        ).fetchall():
            kat_sum.setdefault(r["category"], {})[r["semester"]] = r["p"]
        probanden.append(
            {
                "pseudonym": s["real_name"],  # "Stud. N" – bereits pseudonym
                "semester": sems,
                "kategorien_summen": kat_sum,
            }
        )

    export = {
        "meta": {
            "projekt": "Projekt 2 – KI-gestützte Analyse klinischer Lernverläufe (Zahnmedizin, IK I–IV)",
            "stand": "2026-08-10",
            "quelle": "AuswertungKursleistungenIKIV SoSe26_korrigiert.xlsx (beide Stände zellidentisch geprüft) via ki-kons-carolinum-2026/projekt2/leistungen.db",
            "regeln": {
                "punktregel": "1 Punkt ≈ 45 Minuten klinische Arbeitszeit",
                "ampel": ">= 75 % gut, 50–75 % mittel, < 50 % gering (Ziel-Erreichung je Kategorie)",
                "gesamtziel_punkte": TOTAL_TARGET,
                "semester": SEMESTERS,
                "kursstruktur": "je IK 14 Kurswochen",
            },
            "bekannte_luecken": [
                "IK IV (SoSe26) fehlt in der Quelle – laufendes/nicht erfasstes Semester",
                "Schwierigkeit/Zeitbedarf sind DEMO-Platzhalter (heuristisch); Lehrenden-Konsens (3 Rater) steht aus",
                "Punkte sind je Semester aggregiert – keine Einzeltermine/Reihenfolgen innerhalb des Semesters",
                "Einträge mit 'hinweis' sind nicht aufgeschlüsselte Blocksummen (Leistungsart im Block unbekannt)",
            ],
        },
        "katalog": katalog,
        "probanden": probanden,
    }

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(export, f, ensure_ascii=False, indent=1)
print("Export geschrieben:", OUT)
print(
    "Probanden:",
    len(export["probanden"]),
    "· Katalog-Leistungen:",
    sum(len(k["leistungen"]) for k in katalog),
)
