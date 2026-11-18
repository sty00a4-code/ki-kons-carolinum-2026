"""Vorlesungsabgleiche mit ihren Folien speichern und laden.

Die PDF-Datei liegt getrennt in der Tabelle vorlesungen, damit Listen sie nicht
laden. Je Folie stehen Text, Vorschaubild, Bildbeschreibung und Antwort in der
Tabelle folien; solange antwort NULL ist, ist die Folie offen.
"""

from __future__ import annotations

import dataclasses
import sqlite3
from dataclasses import dataclass

from .. import db
from ..dokumente import Textdatei
from ..security import new_token
from .pdf import Seite

MAX_TITEL = 160

_ANLEGEN = """
insert into folienabgleiche (
    token, titel, ziel, modell, bildmodell, temperatur, prompt,
    vorlesung_name, ziele_name, ziele_text, status,
    erstellt_von, erstellt_am, aktualisiert_am
) values (
    :token, :titel, :ziel, :modell, :bildmodell, :temperatur, :prompt,
    :vorlesung_name, :ziele_name, :ziele_text, 'laeuft',
    :erstellt_von, :zeit, :zeit
)
"""
_FOLIEN_KOPIEREN = """
insert into folien (abgleich_id, nr, folientext, vorschau, bildbeschreibung)
select :neu, nr, folientext, vorschau, case when :bilder then bildbeschreibung end
from folien where abgleich_id = :alt
"""


@dataclass(frozen=True)
class Einstellungen:
    """Womit und wie abgeglichen wird."""

    ziel: str
    modell: str
    bildmodell: str | None = None
    temperatur: float | None = None
    prompt: str | None = None


@dataclass(frozen=True)
class NeuerAbgleich:
    """Werte eines neuen Abgleichs; ziele ist die Lernziel- oder Prüfziel-Datei."""

    titel: str
    einstellungen: Einstellungen
    vorlesung_name: str
    ziele: Textdatei
    erstellt_von: str | None = None


def anlegen(
    con: sqlite3.Connection, neu: NeuerAbgleich, pdf: bytes, seiten: list[Seite]
) -> tuple[int, str]:
    """Legt einen Abgleich mit Vorlesung und Folien an und liefert (ID, Token).

    Committet nicht.
    """
    kennung, token = _einfuegen(con, neu)
    con.execute("insert into vorlesungen (abgleich_id, pdf) values (?, ?)", (kennung, pdf))
    con.executemany(
        "insert into folien (abgleich_id, nr, folientext, vorschau) values (?, ?, ?, ?)",
        [(kennung, nr, seite.text, seite.vorschau) for nr, seite in enumerate(seiten, 1)],
    )
    return kennung, token


def kopieren(
    con: sqlite3.Connection, alt: int, neu: NeuerAbgleich, *, bilder: bool
) -> tuple[int, str]:
    """Legt einen Abgleich mit Vorlesung und Folien des Abgleichs alt an.

    Mit bilder werden die Bildbeschreibungen übernommen. Liefert (ID, Token),
    committet nicht.
    """
    kennung, token = _einfuegen(con, neu)
    con.execute(
        "insert into vorlesungen (abgleich_id, pdf) "
        "select ?, pdf from vorlesungen where abgleich_id = ?",
        (kennung, alt),
    )
    con.execute(_FOLIEN_KOPIEREN, {"neu": kennung, "alt": alt, "bilder": bilder})
    return kennung, token


def _einfuegen(con: sqlite3.Connection, neu: NeuerAbgleich) -> tuple[int, str]:
    token = new_token()
    ziele_name, ziele_text = neu.ziele
    werte = dataclasses.asdict(neu.einstellungen) | {
        "token": token,
        "titel": neu.titel[:MAX_TITEL],
        "vorlesung_name": neu.vorlesung_name,
        "ziele_name": ziele_name,
        "ziele_text": ziele_text,
        "erstellt_von": neu.erstellt_von,
        "zeit": db.jetzt(),
    }
    return db.neue_id(con.execute(_ANLEGEN, werte)), token


def holen(con: sqlite3.Connection, token: str) -> sqlite3.Row | None:
    """Lädt einen Abgleich über sein Token."""
    zeile: sqlite3.Row | None = con.execute(
        "select * from folienabgleiche where token = ?", (token,)
    ).fetchone()
    return zeile


def nach_id(con: sqlite3.Connection, kennung: int) -> sqlite3.Row:
    """Lädt einen Abgleich über seine ID, LookupError, wenn es ihn nicht gibt."""
    zeile: sqlite3.Row | None = con.execute(
        "select * from folienabgleiche where id = ?", (kennung,)
    ).fetchone()
    if zeile is None:
        raise LookupError(f"Vorlesungsabgleich {kennung} fehlt")
    return zeile


def alle(con: sqlite3.Connection) -> list[sqlite3.Row]:
    """Alle Abgleiche, der neueste zuerst."""
    return con.execute(
        "select * from folienabgleiche order by erstellt_am desc, id desc"
    ).fetchall()


def folien(con: sqlite3.Connection, kennung: int) -> list[sqlite3.Row]:
    """Nummer, Text, Bildbeschreibung und Antwort aller Folien eines Abgleichs."""
    return con.execute(
        "select nr, folientext, bildbeschreibung, antwort from folien "
        "where abgleich_id = ? order by nr",
        (kennung,),
    ).fetchall()


def offene(con: sqlite3.Connection, kennung: int) -> list[sqlite3.Row]:
    """Folien ohne Antwort, in der Reihenfolge der Vorlesung."""
    return con.execute(
        "select nr, folientext, bildbeschreibung from folien "
        "where abgleich_id = ? and antwort is null order by nr",
        (kennung,),
    ).fetchall()


def fortschritt(con: sqlite3.Connection, kennung: int) -> tuple[int, int]:
    """Liefert (bearbeitete Folien, alle Folien)."""
    bearbeitet, gesamt = con.execute(
        "select count(antwort), count(*) from folien where abgleich_id = ?", (kennung,)
    ).fetchone()
    return int(bearbeitet), int(gesamt)


def vorschau(con: sqlite3.Connection, kennung: int, nr: int) -> bytes | None:
    """Vorschaubild einer Folie als JPEG."""
    zeile = con.execute(
        "select vorschau from folien where abgleich_id = ? and nr = ?", (kennung, nr)
    ).fetchone()
    return bytes(zeile[0]) if zeile and zeile[0] else None


def pdf_datei(con: sqlite3.Connection, kennung: int) -> bytes | None:
    """Die PDF-Datei der Vorlesung."""
    zeile = con.execute("select pdf from vorlesungen where abgleich_id = ?", (kennung,)).fetchone()
    return bytes(zeile[0]) if zeile else None


def bild_speichern(con: sqlite3.Connection, kennung: int, nr: int, text: str) -> None:
    """Speichert die Bildbeschreibung einer Folie und committet."""
    con.execute(
        "update folien set bildbeschreibung = ? where abgleich_id = ? and nr = ?",
        (text, kennung, nr),
    )
    con.commit()


def antwort_speichern(con: sqlite3.Connection, kennung: int, nr: int, text: str) -> None:
    """Speichert die Antwort zu einer Folie und committet."""
    con.execute(
        "update folien set antwort = ? where abgleich_id = ? and nr = ?", (text, kennung, nr)
    )
    con.commit()


def lebenszeichen(con: sqlite3.Connection, kennung: int) -> bool:
    """Aktualisiert den Zeitstempel eines laufenden Abgleichs und committet.

    Liefert False, wenn der Abgleich gelöscht ist oder nicht mehr läuft.
    """
    cur = con.execute(
        "update folienabgleiche set aktualisiert_am = ? where id = ? and status = 'laeuft'",
        (db.jetzt(), kennung),
    )
    con.commit()
    return cur.rowcount > 0


def fertig(con: sqlite3.Connection, kennung: int) -> None:
    """Beendet einen laufenden Abgleich und committet."""
    con.execute(
        "update folienabgleiche set status = 'fertig', aktualisiert_am = ? "
        "where id = ? and status = 'laeuft'",
        (db.jetzt(), kennung),
    )
    con.commit()


def fehler(con: sqlite3.Connection, kennung: int, meldung: str) -> None:
    """Beendet einen laufenden Abgleich mit einer Fehlermeldung und committet."""
    con.execute(
        "update folienabgleiche set status = 'fehler', fehler = ?, aktualisiert_am = ? "
        "where id = ? and status = 'laeuft'",
        (meldung, db.jetzt(), kennung),
    )
    con.commit()


def fortsetzen(con: sqlite3.Connection, kennung: int) -> bool:
    """Setzt einen abgebrochenen Abgleich wieder auf laufend, ohne zu committen.

    Liefert False, wenn der Abgleich nicht mehr abgebrochen ist, etwa weil eine
    andere Anfrage ihn schon fortgesetzt hat.
    """
    cur = con.execute(
        "update folienabgleiche set status = 'laeuft', fehler = null, aktualisiert_am = ? "
        "where id = ? and status = 'fehler'",
        (db.jetzt(), kennung),
    )
    return cur.rowcount > 0


def erste_offene(con: sqlite3.Connection, kennung: int) -> int | None:
    """Nummer der ersten Folie ohne Antwort, None, wenn alle bearbeitet sind."""
    zeile = con.execute(
        "select min(nr) from folien where abgleich_id = ? and antwort is null", (kennung,)
    ).fetchone()
    return int(zeile[0]) if zeile and zeile[0] is not None else None


def loeschen(con: sqlite3.Connection, kennung: int) -> None:
    """Löscht einen Abgleich mit Vorlesung und Folien, ohne zu committen."""
    con.execute("delete from folienabgleiche where id = ?", (kennung,))
