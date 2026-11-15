"""Durchlauf einer Zuordnung mit dem KI-Dienst.

Die Anfrage läuft gestreamt in einem Thread des Hintergrunds. Der bisher
empfangene Text wird regelmäßig gespeichert, die Ergebnisseite fragt den
Stand ab.
"""

from __future__ import annotations

import functools
import sqlite3
from contextlib import closing

from flask import Flask

from .. import db, hintergrund, ki, pruefziele
from ..config import ki_einstellungen
from . import speicher

ART = "zuordnung"
PROMPT_DATEI = pruefziele.DATEN / "prompt_kategorie1.txt"


@functools.cache
def standard_prompt() -> str:
    """Der vorgegebene Prompt für Kategorie 1."""
    return PROMPT_DATEI.read_text(encoding="utf-8").strip()


def nachricht(zuordnung: sqlite3.Row) -> str:
    """Baut die Nutzernachricht aus Prüfziel-Liste, Lernzielen, Vorlesung und Prompt.

    Die Nummern der Dokumente entsprechen den Verweisen im Prompt.
    """
    liste = pruefziele.liste(zuordnung["pruefziele_liste"])
    teile = [
        f"Dokument 1: Prüfziele {liste.titel}\n\n{liste.text_fuer_modell()}",
        f"Dokument 2: Lernziele ({zuordnung['lernziele_name']})\n\n{zuordnung['lernziele_text']}",
    ]
    if zuordnung["vorlesung_text"]:
        teile.append(
            f"Dokument 3: Vorlesung ({zuordnung['vorlesung_name']})\n\n"
            f"{zuordnung['vorlesung_text']}"
        )
    teile.append(zuordnung["prompt"])
    return "\n\n".join(teile)


def starten(kennung: int) -> None:
    """Startet den Durchlauf einer angelegten Zuordnung im Hintergrund."""
    hintergrund.verwaltung().starten(
        hintergrund.Durchlauf(ART, kennung, ausfuehren, fehler_speichern)
    )


def ausfuehren(app: Flask, kennung: int) -> None:
    """Fragt den KI-Dienst an und speichert Zwischenstände und Antwort."""
    with closing(db.verbindung(app.config["DATABASE"])) as con:
        zuordnung = speicher.nach_id(con, kennung)
        anfrage = ki.Anfrage(zuordnung["modell"], zuordnung["temperatur"], nachricht(zuordnung))
        try:
            antwort = ki.abrufen(
                ki_einstellungen(app),
                anfrage,
                functools.partial(_zwischenstand, con, kennung),
            )
        except ki.KiFehler as exc:
            speicher.fehler(con, kennung, str(exc))
        else:
            speicher.fertig(con, kennung, antwort)


def _zwischenstand(con: sqlite3.Connection, kennung: int, text: str) -> None:
    """Speichert den Zwischenstand und bricht ab, wenn die Zuordnung nicht mehr läuft."""
    if not speicher.zwischenstand(con, kennung, text):
        raise hintergrund.Beendet


def fehler_speichern(app: Flask, kennung: int, meldung: str) -> None:
    """Beendet den Durchlauf nach einem unerwarteten Fehler."""
    with closing(db.verbindung(app.config["DATABASE"])) as con:
        speicher.fehler(con, kennung, meldung)
