"""Prüfung von Formulareingaben, gemeinsam für alle Seiten.

Alle Prüfungen melden Fehler als EingabeFehler mit einer Meldung für die Oberfläche.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from flask import request
from werkzeug.datastructures import FileStorage

from . import dokumente, formate
from .config import Modell
from .fehler import EingabeFehler
from .ki import MAX_TEMPERATUR

MIN_PROMPT = 10
MAX_PROMPT = 20_000


def formularwerte(vorgaben: Mapping[str, str]) -> dict[str, str]:
    """Liefert die abgeschickten Werte der Felder aus vorgaben, ohne Leerraum am Rand.

    Ohne POST-Anfrage bleiben die Vorgaben stehen, fehlende Felder sind leer.
    """
    if request.method != "POST":
        return dict(vorgaben)
    return {feld: request.form.get(feld, "").strip() for feld in vorgaben}


def prompt_pruefen(prompt: str) -> str:
    """Prüft die Länge des Prompts und liefert ihn unverändert."""
    if len(prompt) < MIN_PROMPT:
        raise EingabeFehler(f"Der Prompt muss mindestens {MIN_PROMPT} Zeichen lang sein.")
    if len(prompt) > MAX_PROMPT:
        raise EingabeFehler(f"Der Prompt ist länger als {MAX_PROMPT} Zeichen.")
    return prompt


def temperatur_lesen(text: str) -> float:
    """Liest eine Temperatur zwischen 0 und MAX_TEMPERATUR, auch mit Dezimalkomma."""
    try:
        wert = float((text or "0").replace(",", "."))
    except ValueError as exc:
        raise EingabeFehler("Die Temperatur ist keine Zahl.") from exc
    if not 0 <= wert <= MAX_TEMPERATUR:
        raise EingabeFehler(f"Die Temperatur muss zwischen 0 und {MAX_TEMPERATUR:g} liegen.")
    return wert


def modell_pruefen(modell: str, auswahl: Iterable[Modell], bezeichnung: str = "Modell") -> str:
    """Prüft, ob das Modell in der Auswahl steht, und liefert seine ID."""
    if modell not in dict(auswahl):
        raise EingabeFehler(f"Bitte ein {bezeichnung} aus der Liste wählen.")
    return modell


def datei(feld: str) -> FileStorage | None:
    """Liefert die hochgeladene Datei eines Feldes oder None, wenn keine gewählt ist."""
    hochgeladen = request.files.get(feld)
    return hochgeladen if hochgeladen and hochgeladen.filename else None


def dateiinhalt(feld: str, meldung: str) -> tuple[str, bytes]:
    """Liefert (Dateiname, Inhalt) einer Pflichtdatei, sonst EingabeFehler mit meldung."""
    hochgeladen = datei(feld)
    if hochgeladen is None:
        raise EingabeFehler(meldung)
    return dokumente.dateiname(hochgeladen.filename), hochgeladen.read()


def dateitext(
    feld: str, bezeichnung: str, max_zeichen: int | None = None
) -> dokumente.Textdatei | None:
    """Liefert Name und Text einer hochgeladenen PDF- oder Textdatei oder None.

    Mit max_zeichen darf der Text höchstens so viele Zeichen haben.
    """
    hochgeladen = datei(feld)
    if hochgeladen is None:
        return None
    name = dokumente.dateiname(hochgeladen.filename)
    text = dokumente.text_lesen(name, hochgeladen.read(), bezeichnung)
    if max_zeichen is not None and len(text) > max_zeichen:
        raise EingabeFehler(
            f"{bezeichnung}: Die Datei hat {formate.zahl(len(text))} Zeichen, erlaubt sind "
            f"{formate.zahl(max_zeichen)}. Bitte nur das passende Kapitel hochladen."
        )
    return dokumente.Textdatei(name, text)


def pflichttext(feld: str, bezeichnung: str, max_zeichen: int | None = None) -> dokumente.Textdatei:
    """Wie dateitext(), aber die Datei muss gewählt sein."""
    gelesen = dateitext(feld, bezeichnung, max_zeichen)
    if gelesen is None:
        raise EingabeFehler(f"{bezeichnung}: Bitte eine Datei auswählen.")
    return gelesen
