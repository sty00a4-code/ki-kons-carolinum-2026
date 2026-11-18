"""Durchläufe des KI-Dienstes im Hintergrund.

Vorlesungsabgleiche laufen in eigenen Threads mit eigener Datenbankverbindung.
Höchstens MAX_GLEICHZEITIG Durchläufe laufen zugleich.
Ein Durchlauf, der ABGEBROCHEN_NACH_MINUTEN lang kein Lebenszeichen gibt,
gilt als abgebrochen, etwa nach einem Neustart des Servers.

Ein Durchlauf, dessen Datensatz gelöscht wurde oder nicht mehr läuft, endet
mit der Ausnahme Beendet; zu speichern gibt es dann nichts mehr.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from flask import Flask, current_app

from . import db
from .fehler import EingabeFehler

MAX_GLEICHZEITIG = 2
ABGEBROCHEN_NACH_MINUTEN = 10
ABBRUCH_MELDUNG = f"Abgebrochen: {ABGEBROCHEN_NACH_MINUTEN} Minuten ohne Antwort vom KI-Dienst."

_LAUFENDE = """
select count(*) from folienabgleiche
where status = 'laeuft' and aktualisiert_am >= :grenze
"""
_VERWAISTE = """
update folienabgleiche set status = 'fehler', fehler = :meldung
where status = 'laeuft' and aktualisiert_am < :grenze
"""


class Beendet(Exception):
    """Der Durchlauf wurde gelöscht oder läuft nicht mehr."""


@dataclass(frozen=True)
class Durchlauf:
    """Ein Durchlauf für den Hintergrund.

    ausfuehren(app, kennung) erledigt die Arbeit und fängt die erwarteten
    Fehler selbst ab. Bei einem unerwarteten Fehler speichert
    fehler_speichern(app, kennung, meldung) den Abbruch.
    """

    art: str
    kennung: int
    ausfuehren: Callable[[Flask, int], None]
    fehler_speichern: Callable[[Flask, int, str], None]

    @property
    def name(self) -> str:
        """Name des Threads, etwa "folien-3"."""
        return f"{self.art}-{self.kennung}"


class Hintergrund:
    """Startet Durchläufe als Threads und merkt sich die laufenden."""

    def __init__(self, app: Flask) -> None:
        self._app = app
        self._aktiv: set[str] = set()
        self._sperre = threading.Lock()

    def starten(self, durchlauf: Durchlauf) -> threading.Thread:
        """Startet den Durchlauf in einem eigenen Thread.

        RuntimeError, wenn derselbe Durchlauf in diesem Prozess schon arbeitet.
        """
        with self._sperre:
            if durchlauf.name in self._aktiv:
                raise RuntimeError(f"Durchlauf {durchlauf.name} arbeitet schon")
            self._aktiv.add(durchlauf.name)
        thread = threading.Thread(
            target=self._ausfuehren, args=(durchlauf,), name=durchlauf.name, daemon=True
        )
        thread.start()
        return thread

    def laeuft(self, art: str, kennung: int) -> bool:
        """Gibt an, ob der Thread eines Durchlaufs in diesem Prozess noch arbeitet."""
        with self._sperre:
            return f"{art}-{kennung}" in self._aktiv

    def _ausfuehren(self, durchlauf: Durchlauf) -> None:
        try:
            durchlauf.ausfuehren(self._app, durchlauf.kennung)
        except Beendet:
            self._app.logger.info("Durchlauf %s beendet, er läuft nicht mehr", durchlauf.name)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            # Grenze des Threads: Jeder Fehler wird protokolliert und am Durchlauf gespeichert.
            self._app.logger.exception("Durchlauf %s fehlgeschlagen", durchlauf.name)
            meldung = f"Unerwarteter Fehler ({type(exc).__name__})."
            durchlauf.fehler_speichern(self._app, durchlauf.kennung, meldung)
        finally:
            with self._sperre:
                self._aktiv.discard(durchlauf.name)


def einrichten(app: Flask) -> None:
    """Meldet die Verwaltung der Hintergrund-Durchläufe bei der App an."""
    app.extensions["hintergrund"] = Hintergrund(app)


def verwaltung() -> Hintergrund:
    """Liefert die Verwaltung der Hintergrund-Durchläufe der laufenden App."""
    return cast(Hintergrund, current_app.extensions["hintergrund"])


def laufende(con: sqlite3.Connection) -> int:
    """Anzahl der laufenden Vorlesungsabgleiche."""
    zeile = con.execute(_LAUFENDE, {"grenze": db.vor_minuten(ABGEBROCHEN_NACH_MINUTEN)}).fetchone()
    return int(zeile[0])


def verwaiste_beenden(con: sqlite3.Connection) -> int:
    """Markiert Durchläufe ohne Lebenszeichen als abgebrochen und committet.

    Liefert die Anzahl der beendeten Durchläufe.
    """
    anzahl = _verwaiste_markieren(con)
    con.commit()
    return anzahl


def platz_pruefen(con: sqlite3.Connection) -> None:
    """Beendet verwaiste Durchläufe und prüft, ob ein weiterer starten darf.

    Danach ist eine Schreibtransaktion offen, die der Aufrufer mit dem neuen
    Durchlauf committet. Bis dahin wartet jede andere Anfrage, die einen
    Durchlauf anlegen will; zwei Anfragen belegen so nie zugleich den letzten
    Platz. Die Transaktion sollte deshalb kurz sein.
    """
    con.execute("begin immediate")
    _verwaiste_markieren(con)
    if laufende(con) >= MAX_GLEICHZEITIG:
        con.commit()
        raise EingabeFehler(
            f"Es laufen schon {MAX_GLEICHZEITIG} Durchläufe. Bitte warten, "
            "bis einer davon fertig ist."
        )


def _verwaiste_markieren(con: sqlite3.Connection) -> int:
    werte = {"meldung": ABBRUCH_MELDUNG, "grenze": db.vor_minuten(ABGEBROCHEN_NACH_MINUTEN)}
    return con.execute(_VERWAISTE, werte).rowcount
