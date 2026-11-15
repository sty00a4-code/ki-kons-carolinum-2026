"""Zuordnungen in der Tabelle auswertungen anlegen, laden und fortschreiben.

Gespeichert wird die Antwort des Modells als Text; ergebnis() wertet sie bei
jedem Aufruf mit der aktuellen Prüfziel-Liste aus.
"""

from __future__ import annotations

import dataclasses
import sqlite3
from dataclasses import dataclass

from .. import db, pruefziele
from ..ki import Antwort
from ..security import new_token
from .auswertung import Ergebnis, auswerten

MAX_TITEL = 160
# Ein Durchlauf in der App beginnt laufend, ein übernommenes Ergebnis ist fertig.
STATUS_NACH_QUELLE = {"ki": "laeuft", "import": "fertig"}

_ANLEGEN = """
insert into auswertungen (
    token, titel, kategorie, modell, temperatur, prompt, pruefziele_liste,
    vorlesung_name, vorlesung_text, lernziele_name, lernziele_text, quelle,
    quelle_hinweis, status, rohantwort, erstellt_von, erstellt_am, aktualisiert_am
) values (
    :token, :titel, :kategorie, :modell, :temperatur, :prompt, :pruefziele_liste,
    :vorlesung_name, :vorlesung_text, :lernziele_name, :lernziele_text, :quelle,
    :quelle_hinweis, :status, :rohantwort, :erstellt_von, :zeit, :zeit
)
"""


@dataclass(frozen=True)
class NeueZuordnung:  # pylint: disable=too-many-instance-attributes
    """Werte einer neuen Zuordnung, die Spalten der Tabelle auswertungen.

    quelle ist "ki" für einen Durchlauf in der App oder "import" für ein
    übernommenes Excel-Blatt, quelle_hinweis nennt dann Datei und Blatt.
    """

    titel: str
    modell: str
    quelle: str
    pruefziele_liste: str = pruefziele.STANDARD
    kategorie: int = 1
    temperatur: float | None = None
    prompt: str | None = None
    vorlesung_name: str | None = None
    vorlesung_text: str | None = None
    lernziele_name: str | None = None
    lernziele_text: str | None = None
    quelle_hinweis: str | None = None
    rohantwort: str = ""
    erstellt_von: str | None = None


def anlegen(con: sqlite3.Connection, neu: NeueZuordnung) -> tuple[int, str]:
    """Legt eine Zuordnung an und liefert (ID, Token), ohne zu committen."""
    token = new_token()
    werte = dataclasses.asdict(neu) | {
        "token": token,
        "titel": neu.titel[:MAX_TITEL],
        "status": STATUS_NACH_QUELLE[neu.quelle],
        "zeit": db.jetzt(),
    }
    return db.neue_id(con.execute(_ANLEGEN, werte)), token


def holen(con: sqlite3.Connection, token: str) -> sqlite3.Row | None:
    """Lädt eine Zuordnung über ihr Token."""
    zeile: sqlite3.Row | None = con.execute(
        "select * from auswertungen where token = ?", (token,)
    ).fetchone()
    return zeile


def nach_id(con: sqlite3.Connection, kennung: int) -> sqlite3.Row:
    """Lädt eine Zuordnung über ihre ID, LookupError, wenn es sie nicht gibt."""
    zeile: sqlite3.Row | None = con.execute(
        "select * from auswertungen where id = ?", (kennung,)
    ).fetchone()
    if zeile is None:
        raise LookupError(f"Zuordnung {kennung} fehlt")
    return zeile


def alle(con: sqlite3.Connection) -> list[sqlite3.Row]:
    """Alle Zuordnungen, die neueste zuerst."""
    return con.execute("select * from auswertungen order by erstellt_am desc, id desc").fetchall()


def fertige(con: sqlite3.Connection) -> list[sqlite3.Row]:
    """Fertige Zuordnungen mit Antwort, die neueste zuerst."""
    return con.execute(
        "select * from auswertungen where status = 'fertig' and rohantwort != '' "
        "order by erstellt_am desc, id desc"
    ).fetchall()


def loeschen(con: sqlite3.Connection, kennung: int) -> None:
    """Löscht eine Zuordnung, ohne zu committen."""
    con.execute("delete from auswertungen where id = ?", (kennung,))


def zwischenstand(con: sqlite3.Connection, kennung: int, text: str) -> bool:
    """Speichert den bisher empfangenen Text eines laufenden Durchlaufs und committet.

    Liefert False, wenn die Zuordnung gelöscht ist oder nicht mehr läuft.
    """
    cur = con.execute(
        "update auswertungen set rohantwort = ?, aktualisiert_am = ? "
        "where id = ? and status = 'laeuft'",
        (text, db.jetzt(), kennung),
    )
    con.commit()
    return cur.rowcount > 0


def fertig(con: sqlite3.Connection, kennung: int, antwort: Antwort) -> None:
    """Speichert die vollständige Antwort eines laufenden Durchlaufs und committet."""
    con.execute(
        "update auswertungen set status = 'fertig', rohantwort = ?, abbruch = ?, "
        "aktualisiert_am = ? where id = ? and status = 'laeuft'",
        (antwort.text, antwort.abbruch, db.jetzt(), kennung),
    )
    con.commit()


def fehler(con: sqlite3.Connection, kennung: int, meldung: str) -> None:
    """Beendet einen laufenden Durchlauf mit einer Fehlermeldung und committet."""
    con.execute(
        "update auswertungen set status = 'fehler', fehler = ?, aktualisiert_am = ? "
        "where id = ? and status = 'laeuft'",
        (meldung, db.jetzt(), kennung),
    )
    con.commit()


def ergebnis(zuordnung: sqlite3.Row, liste: pruefziele.Liste | None = None) -> Ergebnis:
    """Wertet die gespeicherte Antwort einer Zuordnung aus."""
    liste = liste or pruefziele.liste(zuordnung["pruefziele_liste"])
    return auswerten(zuordnung["rohantwort"], liste, zuordnung["lernziele_text"])
