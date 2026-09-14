"""SQLite-Zugriff.

Requests nutzen get_db(), Hintergrund-Threads öffnen mit verbindung() eine
eigene Verbindung. Der WAL-Modus erlaubt gleichzeitiges Lesen und Schreiben.
"""

import sqlite3
import time

from flask import current_app, g

ZEITFORMAT = "%Y-%m-%dT%H:%M:%S"


def verbindung(pfad):
    con = sqlite3.connect(pfad, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("pragma foreign_keys = on")
    return con


def get_db():
    if "db" not in g:
        g.db = verbindung(current_app.config["DATABASE"])
        if not current_app.extensions.get("db_angelegt"):
            g.db.execute("pragma journal_mode = wal")
            g.db.executescript(_schema())
            current_app.extensions["db_angelegt"] = True
    return g.db


def close_db(_exc=None):
    con = g.pop("db", None)
    if con is not None:
        con.close()


def _schema():
    with current_app.open_resource("schema.sql") as fh:
        return fh.read().decode("utf-8")


def jetzt():
    return vor_minuten(0)


def vor_minuten(minuten):
    """Liefert die lokale Zeit vor der angegebenen Anzahl Minuten im Format der Datenbank."""
    return time.strftime(ZEITFORMAT, time.localtime(time.time() - minuten * 60))


def init_app(app):
    app.teardown_appcontext(close_db)
