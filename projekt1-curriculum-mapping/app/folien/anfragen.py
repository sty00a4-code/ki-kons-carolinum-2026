"""Anfragen an den KI-Dienst für eine Folie: Bildbeschreibung und Zuordnung."""

from __future__ import annotations

import base64
import functools
import sqlite3
from pathlib import Path
from typing import NamedTuple

from .. import ki
from .katalog import Katalog

# Vorgegebene Prompts je Zielart
DATEN = Path(__file__).resolve().parent.parent / "daten"
BILD_PROMPT = "Interpretiere das Bild in einem Satz!"


class Folieninhalt(NamedTuple):
    """Nummer, Text und Bildbeschreibung einer Folie."""

    nr: int
    text: str
    bild: str | None


@functools.cache
def standard_prompt(ziel: str) -> str:
    """Der vorgegebene Prompt für den Abgleich mit Lernzielen oder Prüfzielen."""
    datei = DATEN / f"prompt_folien_{ziel}.txt"
    return datei.read_text(encoding="utf-8").strip()


def bild_anfrage(abgleich: sqlite3.Row, jpeg: bytes) -> ki.Anfrage:
    """Bittet das Bildmodell, eine gerenderte Folie in einem Satz zu beschreiben."""
    url = "data:image/jpeg;base64," + base64.b64encode(jpeg).decode("ascii")
    inhalt: ki.Inhalt = [
        {"type": "text", "text": BILD_PROMPT},
        {"type": "image_url", "image_url": {"url": url}},
    ]
    return ki.Anfrage(abgleich["bildmodell"], abgleich["temperatur"], inhalt)


def zuordnungs_anfrage(
    abgleich: sqlite3.Row, ziele: Katalog, folie: Folieninhalt, gesamt: int
) -> ki.Anfrage:
    """Fragt nach den Zielen einer Folie: Ziel-Liste, Folientext, Bildbeschreibung, Prompt."""
    teile = [
        f"{ziele.titel}\n\n{ziele.text}",
        f"Folie {folie.nr} von {gesamt}",
        f"Textinhalt: {folie.text or '(kein Text)'}",
    ]
    if folie.bild:
        teile.append(f"Bild: {folie.bild}")
    teile.append(abgleich["prompt"])
    return ki.Anfrage(abgleich["modell"], abgleich["temperatur"], "\n\n".join(teile))
