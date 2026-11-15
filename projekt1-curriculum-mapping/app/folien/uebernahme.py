"""Fertige Ergebnisse eines Vorlesungsabgleichs aus Excel- oder JSON-Dateien lesen.

Erwartet wird je Folie die Nummer und der Text mit den Zielen, etwa aus dem
Excel-Export eines Abgleichs oder eine JSON-Liste von Objekten mit den
Schlüsseln "folien-nr" und "Zuordnung". Eine Bildbeschreibung wird mit
übernommen.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any, NamedTuple

from .. import excel
from ..fehler import EingabeFehler

BLATT = "Folien"

_FOLIEN_SPALTE = re.compile(r"^(folien?|seite)([\s-]*nr\.?)?$")
_ZIEL_SPALTE = re.compile(r"^(zuordnung|lernziele|prüfziele|pruefziele|ziele|antwort)")
_NUMMER = re.compile(r"\d+")


class ImportFehler(EingabeFehler):
    """Die Ergebnisdatei ist nicht lesbar oder enthält keine Folien."""


class Antworten(NamedTuple):
    """Antworten je Folie {Folie: (Antwort, Bildbeschreibung)}.

    verschoben ist gesetzt, wenn die Datei die Folien ab 0 zählt und die
    Nummern deshalb um 1 erhöht wurden.
    """

    je_folie: dict[int, tuple[str, str | None]]
    verschoben: bool


# Nummer der Folie, Antwort und Bildbeschreibung aus einer Zeile der Datei
_Zeile = tuple[str, str, str | None]


def antworten_aus_datei(daten: bytes, name: str) -> Antworten:
    """Liest Folien und Antworten aus einer Excel- oder JSON-Datei."""
    zeilen = _json_zeilen(daten) if name.lower().endswith(".json") else _excel_zeilen(daten)
    je_folie: dict[int, tuple[str, str | None]] = {}
    for nr_text, antwort, bild in zeilen:
        nummer = _NUMMER.search(nr_text)
        if not nummer:
            continue
        nr = int(nummer.group())
        bisher, bisher_bild = je_folie.get(nr, ("", None))
        je_folie[nr] = ("\n".join(filter(None, (bisher, antwort))), bild or bisher_bild)
    if not je_folie:
        raise ImportFehler(
            "In der Datei stehen keine Folien. Erwartet wird je Folie eine Zeile mit der "
            "Foliennummer (Spalte „Folie“) und den Zielen (Spalte „Lernziele“ oder „Prüfziele“)."
        )
    verschoben = 0 in je_folie
    if verschoben:
        je_folie = {nr + 1: werte for nr, werte in je_folie.items()}
    return Antworten(je_folie, verschoben)


def _json_zeilen(daten: bytes) -> list[_Zeile]:
    try:
        eintraege = json.loads(daten.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ImportFehler("Die Datei ist keine lesbare JSON-Datei.") from exc
    if not isinstance(eintraege, list):
        raise ImportFehler("Die JSON-Datei muss eine Liste mit einem Objekt je Folie enthalten.")
    return [zeile for zeile in map(_json_zeile, eintraege) if zeile]


def _json_zeile(objekt: Any) -> _Zeile | None:
    if not isinstance(objekt, dict):
        return None
    werte = {str(k).strip().lower(): v for k, v in objekt.items()}
    nr = _wert(werte, _FOLIEN_SPALTE.match)
    if nr is None:
        return None
    antwort = _wert(werte, _ZIEL_SPALTE.match)
    if isinstance(antwort, list):
        antwort = "\n".join(str(a).strip() for a in antwort)
    bild = _wert(werte, _ist_bildspalte)
    return str(nr), str(antwort or "").strip(), str(bild or "").strip() or None


def _wert(werte: dict[str, Any], passt: Callable[[str], object]) -> Any:
    """Wert unter dem ersten passenden Schlüssel, sonst None."""
    return next((v for k, v in werte.items() if passt(k)), None)


def _excel_zeilen(daten: bytes) -> list[_Zeile]:
    tabellen = excel.tabellen(daten, "Die Datei ist weder eine Excel-Datei (.xlsx) noch JSON.")
    tabelle = _blatt(tabellen)
    if tabelle is None or not tabelle.zeilen:
        return []
    kopf = [k.lower() for k in tabelle.zeilen[0]]
    nr = _spalte(kopf, _FOLIEN_SPALTE.match)
    ziele = _spalte(kopf, _ZIEL_SPALTE.match)
    if nr is None or ziele is None:
        return []
    bild = _spalte(kopf, _ist_bildspalte)
    ergebnis: list[_Zeile] = []
    for zeile in tabelle.zeilen[1:]:
        z = [*zeile, *[""] * (len(kopf) - len(zeile))]
        ergebnis.append((z[nr], z[ziele], (z[bild] or None) if bild is not None else None))
    return ergebnis


def _blatt(tabellen: list[excel.Tabelle]) -> excel.Tabelle | None:
    """Das Blatt BLATT, sonst das erste Blatt der Datei."""
    return next((t for t in tabellen if t.name == BLATT), tabellen[0] if tabellen else None)


def _ist_bildspalte(name: str) -> bool:
    return name.startswith("bild")


def _spalte(kopf: list[str], passt: Callable[[str], object]) -> int | None:
    return next((i for i, k in enumerate(kopf) if passt(k)), None)
