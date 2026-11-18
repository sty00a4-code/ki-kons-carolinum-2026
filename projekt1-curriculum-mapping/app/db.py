"""SQLite-Zugriff.

Requests nutzen get_db(), Hintergrund-Threads öffnen mit verbindung() eine
eigene Verbindung. Das Schema aus schema.sql wird beim ersten Zugriff
angelegt, der WAL-Modus erlaubt gleichzeitiges Lesen und Schreiben.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from flask import Flask, current_app, g

ZEITFORMAT = "%Y-%m-%dT%H:%M:%S"
WARTEN_AUF_SPERRE_SEKUNDEN = 15
# Datenbank der Anwendung, wenn die Konfiguration keine andere nennt
STANDARD_PFAD = Path(__file__).resolve().parent.parent / "data" / "projekt1.db"


def verbindung(pfad: str) -> sqlite3.Connection:
    """Öffnet eine Verbindung mit Zeilen als sqlite3.Row und aktiven Fremdschlüsseln."""
    con = sqlite3.connect(pfad, timeout=WARTEN_AUF_SPERRE_SEKUNDEN)
    con.row_factory = sqlite3.Row
    con.execute("pragma foreign_keys = on")
    return con


def oeffnen(pfad: Path) -> sqlite3.Connection:
    """Öffnet eine Datenbank ohne App, etwa für Skripte; legt Ordner und Schema an."""
    pfad.parent.mkdir(parents=True, exist_ok=True)
    con = verbindung(str(pfad))
    einrichten(con)
    return con


def get_db() -> sqlite3.Connection:
    """Liefert die Verbindung der laufenden Anfrage und legt beim ersten Mal das Schema an."""
    if "db" not in g:
        g.db = verbindung(current_app.config["DATABASE"])
        if not current_app.extensions.get("db_angelegt"):
            einrichten(g.db)
            current_app.extensions["db_angelegt"] = True
    con: sqlite3.Connection = g.db
    return con


def einrichten(con: sqlite3.Connection) -> None:
    """Schaltet den WAL-Modus ein und legt das Schema an; wiederholbar."""
    con.execute("pragma journal_mode = wal")
    con.executescript(_schema())


def close_db(_exc: BaseException | None = None) -> None:
    """Schließt die Verbindung der Anfrage, falls eine offen ist."""
    con = g.pop("db", None)
    if con is not None:
        con.close()


def neue_id(cursor: sqlite3.Cursor) -> int:
    """Liefert die ID der Zeile, die der Cursor zuletzt eingefügt hat."""
    if cursor.lastrowid is None:
        raise sqlite3.DatabaseError("Die Anweisung hat keine Zeile eingefügt.")
    return cursor.lastrowid


def jetzt() -> str:
    """Liefert die lokale Zeit im Format der Datenbank."""
    return vor_minuten(0)


def vor_minuten(minuten: float) -> str:
    """Liefert die lokale Zeit vor der angegebenen Anzahl Minuten im Format der Datenbank."""
    return time.strftime(ZEITFORMAT, time.localtime(time.time() - minuten * 60))


def init_app(app: Flask) -> None:
    """Schließt die Verbindung am Ende jeder Anfrage."""
    app.teardown_appcontext(close_db)


def _schema() -> str:
    return Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
