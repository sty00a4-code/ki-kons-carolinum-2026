"""Ergebnis-Excel-Dateien übernehmen.

Jedes Blatt entspricht einem Durchlauf. Die Zellen einer Zeile werden zu einer
Antwortzeile im Format des Prompts verbunden und mit derselben Funktion
gelesen wie eine Antwort des Modells.

Enthält ein Blatt eine Kopfzeile mit Prüfziel und Abdeckung, etwa aus dem
Export der App, zählen nur die benannten Spalten. Sonst beginnt die
Antwortzeile in der Spalte mit den Prüfzielen.
"""

from __future__ import annotations

import re
import sqlite3
from collections import Counter
from dataclasses import dataclass
from pathlib import PurePath
from typing import NamedTuple

from .. import excel, pruefziele
from ..dokumente import Textdatei
from ..ki import MAX_TEMPERATUR
from . import speicher
from .antwort import beginnt_mit_pruefziel, lesen

# Kopfzeilen werden in den ersten Zeilen eines Blattes gesucht.
KOPF_SUCHE_ZEILEN = 5

_KOPF = {
    "teil": ("teil",),
    "pruefziel": ("prüfziel", "pruefziel"),
    "abdeckung": ("abdeckung",),
    "begruendung": ("begründung", "begruendung"),
    "lernziele": ("lernziel",),
}
# Temperatur im Blattnamen: eine Zahl nach "Temp" oder eine Dezimalzahl.
# Ganze Zahlen ohne "Temp" sind meist Zählnummern wie in "Tabelle1".
_TEMPERATUR = re.compile(
    r"temp(?:eratur)?\s*[:=]?\s*(\d+(?:[.,]\d+)?)|(?<![\d.,])(\d+[.,]\d+)(?![\d.,])",
    re.IGNORECASE,
)


class Blatt(NamedTuple):
    """Ein Blatt mit Zuordnung: Name, Antworttext und Anzahl der gelesenen Zeilen."""

    name: str
    text: str
    zeilen: int


@dataclass(frozen=True)
class Uebernahme:
    """Angaben zu einer Ergebnis-Excel, die für alle ihre Blätter gelten."""

    modell: str
    pruefziele_liste: str = pruefziele.STANDARD
    titel: str = ""
    prompt: str = ""
    lernziele: Textdatei | None = None
    vorlesung: Textdatei | None = None
    erstellt_von: str | None = None


class Uebernommen(NamedTuple):
    """Ein übernommenes Blatt mit dem Token der neuen Zuordnung."""

    blatt: str
    token: str
    zeilen: int


def blaetter(daten: bytes) -> list[Blatt]:
    """Liefert alle Blätter einer Excel-Datei, in denen eine Zuordnung steht."""
    tabellen = excel.tabellen(daten, "Die Datei ist keine lesbare Excel-Datei (.xlsx).")
    gefunden = [blatt for blatt in map(_blatt, tabellen) if blatt.zeilen]
    if not gefunden:
        raise excel.ExcelFehler(
            "In der Excel-Datei steht keine Zuordnung. Erwartet werden Zeilen mit "
            "Prüfziel, Abdeckung, Begründung und Lernziel-ID."
        )
    return gefunden


def uebernehmen(
    con: sqlite3.Connection, daten: bytes, excel_name: str, angaben: Uebernahme
) -> list[Uebernommen]:
    """Legt für jedes Blatt mit Zuordnung eine Zuordnung an, ohne zu committen."""
    grundname = angaben.titel.strip() or PurePath(excel_name).stem
    vorlesung_name, vorlesung_text = angaben.vorlesung or (None, None)
    lernziele_name, lernziele_text = angaben.lernziele or (None, None)
    angelegt = []
    for blatt in blaetter(daten):
        _, token = speicher.anlegen(
            con,
            speicher.NeueZuordnung(
                titel=f"{grundname} · {blatt.name}",
                modell=angaben.modell,
                quelle="import",
                pruefziele_liste=angaben.pruefziele_liste,
                temperatur=temperatur_aus_name(blatt.name),
                prompt=angaben.prompt.strip() or None,
                vorlesung_name=vorlesung_name,
                vorlesung_text=vorlesung_text,
                lernziele_name=lernziele_name,
                lernziele_text=lernziele_text,
                quelle_hinweis=f"{excel_name}, Blatt {blatt.name}",
                rohantwort=blatt.text,
                erstellt_von=angaben.erstellt_von,
            ),
        )
        angelegt.append(Uebernommen(blatt.name, token, blatt.zeilen))
    return angelegt


def temperatur_aus_name(name: str | None) -> float | None:
    """Liest eine Temperatur aus einem Blattnamen wie "Temp 0,7" oder "mistral 0.5"."""
    treffer = _TEMPERATUR.search(name or "")
    if not treffer:
        return None
    wert = float((treffer.group(1) or treffer.group(2)).replace(",", "."))
    return wert if 0 <= wert <= MAX_TEMPERATUR else None


def _blatt(tabelle: excel.Tabelle) -> Blatt:
    zeilen = [z for z in tabelle.zeilen if any(z)]
    spalten = _kopf_spalten(zeilen)
    if spalten:
        text = "\n".join(filter(None, (_aus_spalten(z, spalten) for z in zeilen)))
    else:
        start = _pruefziel_spalte(zeilen)
        text = "\n".join(_als_antwortzeile(z[start:]) for z in zeilen)
    gelesen, _ = lesen(text)
    return Blatt(tabelle.name, text, len(gelesen))


def _kopf_spalten(zeilen: list[list[str]]) -> dict[str, int] | None:
    """Sucht in den ersten Zeilen eine Kopfzeile und liefert {Feld: Spaltenindex}.

    Fehlen die Spalten Prüfziel oder Abdeckung, ist das Ergebnis None.
    """
    for zeile in zeilen[:KOPF_SUCHE_ZEILEN]:
        spalten: dict[str, int] = {}
        for index, wert in enumerate(zeile):
            kopf = wert.replace("*", "").strip().lower()
            feld = next(
                (f for f, anf in _KOPF.items() if f not in spalten and kopf.startswith(anf)),
                None,
            )
            if feld:
                spalten[feld] = index
        if "pruefziel" in spalten and "abdeckung" in spalten:
            return spalten
    return None


def _aus_spalten(zeile: list[str], spalten: dict[str, int]) -> str:
    """Setzt eine Antwortzeile aus den benannten Spalten zusammen.

    Zeilen, die nur die Prüfziel-Spalte füllen, bleiben ohne Trennzeichen und
    gelten beim Lesen als Überschrift.
    """

    def wert(feld: str) -> str:
        index = spalten.get(feld)
        return zeile[index] if index is not None and index < len(zeile) else ""

    pruefziel = wert("pruefziel")
    teil = wert("teil").upper()
    if teil in ("VI", "VIII") and pruefziel and not pruefziel.upper().startswith("VI"):
        pruefziel = f"{teil} {pruefziel}"
    rest = [wert("abdeckung"), wert("begruendung"), wert("lernziele")]
    if not any(r.strip() for r in rest):
        return pruefziel
    return ";".join(x.replace(";", ",") for x in (pruefziel, *rest))


def _pruefziel_spalte(zeilen: list[list[str]]) -> int:
    """Liefert den Index der Spalte, in der die meisten Zeilen mit einem Prüfziel beginnen."""
    erste = (
        next((i for i, wert in enumerate(zeile) if beginnt_mit_pruefziel(wert)), None)
        for zeile in zeilen
    )
    zaehler = Counter(i for i in erste if i is not None)
    return max(zaehler, key=zaehler.__getitem__, default=0)


def _als_antwortzeile(zellen: list[str]) -> str:
    """Verbindet die Zellen einer Zeile zu einer Antwortzeile.

    Eine einzelne gefüllte Zelle wird unverändert übernommen. Bei mehreren
    Zellen werden Semikolons im Zellinhalt durch Kommas ersetzt.
    """
    zellen = list(zellen)
    while zellen and not zellen[-1]:
        zellen.pop()
    if sum(1 for z in zellen if z) == 1 and zellen[0]:
        return zellen[0]
    return ";".join(z.replace(";", ",") for z in zellen)
