"""Ablauf eines Vorlesungsabgleichs im Hintergrund.

Für jede offene Folie beschreibt zuerst das Bildmodell die gerenderte Folie
in einem Satz, danach nennt das Modell die passenden Ziele. Jede Antwort wird
sofort gespeichert; ein abgebrochener Abgleich lässt sich deshalb an der
Stelle fortsetzen, an der er stehen geblieben ist.
"""

from __future__ import annotations

import sqlite3
import time
from contextlib import closing

from flask import Flask

from .. import db, hintergrund, ki
from ..config import KiEinstellungen, ki_einstellungen
from . import anfragen, pdf, speicher
from .katalog import katalog

ART = "folien"
WIEDERHOLEN_NACH_SEKUNDEN = 5
# Wartezeit nach Status 429 ohne Angabe des Dienstes und Obergrenze für seine Angabe
WARTEN_BEI_UEBERLASTUNG = 60
MAX_WARTEN_SEKUNDEN = 120


def starten(kennung: int) -> None:
    """Startet einen angelegten oder fortgesetzten Abgleich im Hintergrund."""
    hintergrund.verwaltung().starten(
        hintergrund.Durchlauf(ART, kennung, ausfuehren, fehler_speichern)
    )


def laeuft(kennung: int) -> bool:
    """Gibt an, ob der Thread eines Abgleichs in diesem Prozess noch arbeitet."""
    return hintergrund.verwaltung().laeuft(ART, kennung)


def ausfuehren(app: Flask, kennung: int) -> None:
    """Bearbeitet alle offenen Folien eines Abgleichs nacheinander."""
    with closing(db.verbindung(app.config["DATABASE"])) as con:
        try:
            _folien_bearbeiten(con, kennung, ki_einstellungen(app))
        except ki.KiFehler as exc:
            speicher.fehler(con, kennung, _mit_folie(con, kennung, str(exc)))
            return
        speicher.fertig(con, kennung)


def fehler_speichern(app: Flask, kennung: int, meldung: str) -> None:
    """Beendet den Abgleich nach einem unerwarteten Fehler."""
    with closing(db.verbindung(app.config["DATABASE"])) as con:
        speicher.fehler(con, kennung, _mit_folie(con, kennung, meldung))


def _folien_bearbeiten(
    con: sqlite3.Connection, kennung: int, einstellungen: KiEinstellungen
) -> None:
    abgleich = speicher.nach_id(con, kennung)
    ziele = katalog(abgleich)
    _, gesamt = speicher.fortschritt(con, kennung)
    vorlesung = None
    for folie in speicher.offene(con, kennung):
        nr = folie["nr"]
        bild = folie["bildbeschreibung"]
        if abgleich["bildmodell"] and bild is None:
            vorlesung = vorlesung or speicher.pdf_datei(con, kennung) or b""
            anfrage = anfragen.bild_anfrage(abgleich, pdf.seitenbild(vorlesung, nr))
            bild = _fragen(con, kennung, einstellungen, anfrage).strip()
            speicher.bild_speichern(con, kennung, nr, bild)
        inhalt = anfragen.Folieninhalt(nr, folie["folientext"], bild)
        anfrage = anfragen.zuordnungs_anfrage(abgleich, ziele, inhalt, gesamt)
        speicher.antwort_speichern(con, kennung, nr, _fragen(con, kennung, einstellungen, anfrage))


def _fragen(
    con: sqlite3.Connection, kennung: int, einstellungen: KiEinstellungen, anfrage: ki.Anfrage
) -> str:
    """Sendet eine Anfrage und wiederholt sie nach einem Fehler einmal.

    Vor jeder Anfrage gibt der Abgleich ein Lebenszeichen. Meldet der Dienst
    zu viele Anfragen, wartet er vor der Wiederholung so lange, wie der Dienst
    verlangt, höchstens MAX_WARTEN_SEKUNDEN.
    """
    _lebenszeichen(con, kennung)
    try:
        return ki.abrufen(einstellungen, anfrage)
    except ki.KiUeberlastet as exc:
        time.sleep(_wartezeit(exc))
    except ki.KiFehler:
        time.sleep(WIEDERHOLEN_NACH_SEKUNDEN)
    _lebenszeichen(con, kennung)
    return ki.abrufen(einstellungen, anfrage)


def _wartezeit(fehler: ki.KiUeberlastet) -> float:
    if fehler.warten is None:
        return WARTEN_BEI_UEBERLASTUNG
    return min(fehler.warten, MAX_WARTEN_SEKUNDEN)


def _lebenszeichen(con: sqlite3.Connection, kennung: int) -> None:
    """Meldet, dass der Abgleich noch arbeitet, und bricht ab, wenn er nicht mehr läuft."""
    if not speicher.lebenszeichen(con, kennung):
        raise hintergrund.Beendet


def _mit_folie(con: sqlite3.Connection, kennung: int, meldung: str) -> str:
    """Stellt der Meldung die Folie voran, an der der Abgleich stehen geblieben ist."""
    nr = speicher.erste_offene(con, kennung)
    return f"Folie {nr}: {meldung}" if nr else meldung
