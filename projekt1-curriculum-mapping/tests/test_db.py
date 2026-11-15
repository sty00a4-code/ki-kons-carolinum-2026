"""Datenbank: Anlegen und Übernahme älterer Datenbanken."""

import sqlite3
from contextlib import closing
from pathlib import Path

from app import db

SCHEMA = (Path(db.__file__).with_name("schema.sql")).read_text(encoding="utf-8")


def _spalten(con: sqlite3.Connection, tabelle: str) -> list[str]:
    return [zeile[1] for zeile in con.execute(f"pragma table_info({tabelle})")]


def test_einrichten_legt_alle_tabellen_an(tmp_path: Path) -> None:
    """Eine neue Datenbank erhält alle Tabellen; ein zweiter Aufruf ändert nichts."""
    with closing(db.verbindung(str(tmp_path / "neu.db"))) as con:
        db.einrichten(con)
        db.einrichten(con)
        tabellen = {
            z[0] for z in con.execute("select name from sqlite_master where type = 'table'")
        }
    assert {"users", "auswertungen", "folienabgleiche", "folien"} <= tabellen


def test_alte_spaltennamen_werden_umbenannt(tmp_path: Path) -> None:
    """Ältere Datenbanken mit lernziele_name und lernziele_text werden übernommen."""
    alt = SCHEMA.replace("    ziele_name text,", "    lernziele_name text,").replace(
        "    ziele_text text,", "    lernziele_text text,"
    )
    assert alt.count("lernziele_name text,") == 2
    pfad = str(tmp_path / "alt.db")
    with closing(sqlite3.connect(pfad)) as con:
        con.executescript(alt)
        con.execute(
            "insert into folienabgleiche (token, titel, ziel, modell, vorlesung_name, quelle, "
            "status, erstellt_am, aktualisiert_am, lernziele_name, lernziele_text) values "
            "('t', 'Alt', 'lernziele', 'm', 'v.pdf', 'ki', 'fertig', 'x', 'x', 'lz.pdf', 'Text')"
        )
        con.commit()
    with closing(db.verbindung(pfad)) as con:
        db.einrichten(con)
        assert "ziele_name" in _spalten(con, "folienabgleiche")
        assert "lernziele_name" not in _spalten(con, "folienabgleiche")
        zeile = con.execute("select ziele_name, ziele_text from folienabgleiche").fetchone()
    assert tuple(zeile) == ("lz.pdf", "Text")
