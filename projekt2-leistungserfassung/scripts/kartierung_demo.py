"""Kartierung Schwierigkeit & Zeitbedarf – Vorlage + Demo-Platzhalterwerte.

    python -m scripts.kartierung_demo            # schreibt nur die Vorlage (CSV)
    python -m scripts.kartierung_demo --apply    # setzt zusätzlich DEMO-Werte in der DB

Hintergrund (Projektplan Phase 2, "Kartierung: Schwierigkeit & Zeitbedarf pro
Leistung" + "3 Lehrende: Konsensbildung"): Jede Katalog-Leistung braucht einen
konsentierten Schwierigkeitsgrad (1 leicht / 2 mittel / 3 schwer) und einen
Zeitbedarf in Minuten. Diese Werte gibt es noch NICHT – sie müssen von den
3 Lehrenden erhoben werden (Vorlage: docs/kartierung/kartierung_vorlage.csv).

WICHTIG: --apply setzt heuristische DEMO-WERTE (Platzhalter!), damit die
KI-Analyse-Pipeline durchgängig demonstriert werden kann. Zeitbedarf-Heuristik:
Punkte × 45 min (Grundregel der Blauen Liste). Schwierigkeit: fachliche
Schätzung als Platzhalter. Sobald der Lehrenden-Konsens vorliegt: Werte hier
eintragen und --apply erneut ausführen (Einträge werden überschrieben, die
Notiz kennzeichnet Demo-Werte).
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.catalog import CATALOG

# DEMO-Platzhalter Schwierigkeit je Katalog-Code (1 leicht / 2 mittel / 3 schwer).
# KEIN Lehrenden-Konsens! Nur damit die Pipeline demonstrierbar ist.
DEMO_DIFFICULTY = {
    "pa_ait": 3,
    "pa_upt": 1,
    "zhs_fuell_1_2": 2,
    "zhs_fuell_3_4": 2,
    "zhs_fuell_5": 1,
    "zhs_befund": 1,
    "zhs_prophylaxe": 1,
    "endo_aufbereitung": 3,
    "endo_fuellung": 3,
    "endo_revision": 3,
    "kzh_befund": 1,
    "kzh_prophylaxe": 1,
    "kzh_behandlung": 2,
    "proth_krone": 3,
    "proth_bruecke": 3,
    "proth_totalprothese": 3,
    "proth_teilprothese": 3,
    "proth_teleskop": 3,
    "proth_modellguss": 2,
    "proth_interims": 2,
    "proth_unterfuett": 1,
    "proth_remontage": 1,
    "proth_recall": 1,
    "proth_aufbiss": 2,
    "schnitt_inlay": 3,
    "schnitt_reparatur": 1,
    "schnitt_stumpfaufbau": 2,
    "schnitt_stiftaufbau": 2,
    "chir_msh": 1,
    "chir_dvt": 1,
    "chir_impl_beratung": 1,
    "chir_impl_nachsorge": 1,
    "kfo_erstgespraech": 1,
    "kfo_anamnese": 1,
    "kfo_abformung": 1,
    "kfo_modell": 1,
    "kfo_3d": 2,
    "kfo_foto": 1,
    "kfo_roentgen": 2,
    "kfo_plan": 2,
    "kfo_konstruktion": 2,
    "kfo_kontrolle": 1,
}

VORLAGE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "docs",
    "kartierung",
    "kartierung_vorlage.csv",
)


def write_vorlage():
    os.makedirs(os.path.dirname(VORLAGE), exist_ok=True)
    with open(VORLAGE, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(
            [
                "Kategorie",
                "Code",
                "Leistung",
                "Punkte (typisch)",
                "Einheit",
                "Schwierigkeit Lehrende/r A (1-3)",
                "Schwierigkeit Lehrende/r B (1-3)",
                "Schwierigkeit Lehrende/r C (1-3)",
                "KONSENS Schwierigkeit (1-3)",
                "Zeitbedarf Lehrende/r A (min)",
                "Zeitbedarf Lehrende/r B (min)",
                "Zeitbedarf Lehrende/r C (min)",
                "KONSENS Zeitbedarf (min)",
                "Demo-Platzhalter Schwierigkeit",
                "Demo-Platzhalter Zeit (min)",
                "Bemerkung",
            ]
        )
        for category, items in CATALOG:
            for it in items:
                w.writerow(
                    [
                        category,
                        it["code"],
                        it["name"],
                        f"{it['points_min']:g}",
                        it["unit"],
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        DEMO_DIFFICULTY.get(it["code"], ""),
                        int(it["points_min"] * 45),
                        "",
                    ]
                )
    print("Vorlage geschrieben:", VORLAGE)


def apply_demo():
    from app.db import get_db

    app = create_app()
    with app.app_context():
        db = get_db()
        updated = 0
        for code, diff in DEMO_DIFFICULTY.items():
            cur = db.execute(
                "update performances set difficulty = ?, "
                "time_minutes = cast(round(points * 45) as integer), "
                "note = note || ' · Schwierigkeit/Zeit = DEMO-Platzhalter (kein Lehrenden-Konsens)' "
                "where item_code = ? and difficulty is null",
                (diff, code),
            )
            updated += cur.rowcount
        db.commit()
        print(
            f"{updated} Einträge mit Demo-Kartierung versehen (difficulty + time_minutes)."
        )


if __name__ == "__main__":
    write_vorlage()
    if "--apply" in sys.argv:
        apply_demo()
