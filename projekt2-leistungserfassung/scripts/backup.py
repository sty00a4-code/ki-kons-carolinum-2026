"""Backup gegen Datenverlust: kopiert die DB + exportiert genehmigte Daten als CSV.

    python -m scripts.backup

Legt Zeitstempel-Kopien unter backups/ ab (git-ignoriert). Der CSV-Export
enthält nur Pseudonyme, keine Klarnamen.
"""

import csv
import datetime
import os
import shutil
import sqlite3

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, "data", "leistung.db")
OUT = os.path.join(BASE, "backups")


def main():
    if not os.path.exists(DB):
        raise SystemExit(
            f"Keine Datenbank gefunden: {DB} (erst 'python -m scripts.init_db')"
        )
    os.makedirs(OUT, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    db_copy = os.path.join(OUT, f"leistung_{ts}.db")
    shutil.copy2(DB, db_copy)

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "select s.pseudonym, p.semester, p.category, p.item_name, p.count, "
        "p.points, p.status, p.reviewed_at from performances p "
        "join students s on p.student_id = s.id order by s.pseudonym"
    ).fetchall()
    con.close()

    header = [
        "pseudonym",
        "semester",
        "category",
        "item_name",
        "count",
        "points",
        "status",
        "reviewed_at",
    ]
    csv_path = os.path.join(OUT, f"export_{ts}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow([r[k] for k in header])

    print("Backup erstellt:")
    print(" ", db_copy)
    print(" ", csv_path)


if __name__ == "__main__":
    main()
