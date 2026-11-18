"""Datenbank: Anlegen der Tabellen."""

from contextlib import closing
from pathlib import Path

from app import db


def test_einrichten_legt_alle_tabellen_an(tmp_path: Path) -> None:
    """Eine neue Datenbank erhält alle Tabellen; ein zweiter Aufruf ändert nichts."""
    with closing(db.verbindung(str(tmp_path / "neu.db"))) as con:
        db.einrichten(con)
        db.einrichten(con)
        tabellen = {
            z[0] for z in con.execute("select name from sqlite_master where type = 'table'")
        }
    assert {"users", "folienabgleiche", "vorlesungen", "folien"} <= tabellen
