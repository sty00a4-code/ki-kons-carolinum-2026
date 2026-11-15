"""Gemeinsame Bausteine für das Lesen und Schreiben von Excel-Dateien."""

from __future__ import annotations

import datetime
import io
import re
import zipfile
from collections.abc import Iterable, Sequence
from typing import NamedTuple

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.workbook.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from .fehler import EingabeFehler

MIMETYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MAX_TITEL_IM_DATEINAMEN = 80

KOPF_FUELLUNG = PatternFill("solid", fgColor="E6EAF7")
GRUPPE_FUELLUNG = {
    "teil": PatternFill("solid", fgColor="D5DCF2"),
    "bereich": PatternFill("solid", fgColor="EEF1FB"),
    "gruppe": PatternFill("solid", fgColor="F7F8FD"),
}
_UMBRUCH = Alignment(wrap_text=True, vertical="top")
# In XLSX-Dateien nicht erlaubte Steuerzeichen
_STEUERZEICHEN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


class ExcelFehler(EingabeFehler):
    """Die Datei ist keine lesbare Excel-Datei."""


class Tabelle(NamedTuple):
    """Ein Blatt einer Excel-Datei: Name und Zeilen als Texte, siehe zelle()."""

    name: str
    zeilen: list[list[str]]


def tabellen(daten: bytes, meldung: str) -> list[Tabelle]:
    """Liest alle Blätter einer Excel-Datei, sonst ExcelFehler mit meldung."""
    try:
        arbeitsmappe = openpyxl.load_workbook(io.BytesIO(daten), read_only=True, data_only=True)
        try:
            return [
                Tabelle(
                    blatt.title.strip(),
                    [[zelle(w) for w in reihe] for reihe in blatt.iter_rows(values_only=True)],
                )
                for blatt in arbeitsmappe.worksheets
            ]
        finally:
            arbeitsmappe.close()
    except (zipfile.BadZipFile, OSError, KeyError, ValueError, TypeError) as exc:
        raise ExcelFehler(meldung) from exc


def zelle(wert: object) -> str:
    """Liefert den Wert einer Zelle als Text ohne mehrfachen Leerraum.

    Excel wandelt Nummern wie "4.5.2" in das Datum 4.5.2002 um, daraus wird
    wieder die Nummer.
    """
    if wert is None:
        return ""
    if isinstance(wert, datetime.datetime):
        return f"{wert.day}.{wert.month}.{wert.year % 100}"
    if isinstance(wert, float) and wert.is_integer():
        return str(int(wert))
    return re.sub(r"\s+", " ", str(wert)).strip()


def dateiname(praefix: str, titel: str) -> str:
    """Liefert einen Dateinamen wie "Zuordnung Titel.xlsx" ohne problematische Zeichen."""
    titel = re.sub(r"\s+", " ", re.sub(r"[^\w.,() -]+", " ", titel).strip())
    return f"{praefix} {titel[:MAX_TITEL_IM_DATEINAMEN]}.xlsx"


def mappe() -> tuple[Workbook, Worksheet]:
    """Legt eine neue Arbeitsmappe an und liefert sie mit ihrem ersten Blatt."""
    neu = Workbook()
    blatt = neu.active
    if not isinstance(blatt, Worksheet):
        raise TypeError("Neue Arbeitsmappe ohne Tabellenblatt")
    return neu, blatt


def als_bytes(arbeitsmappe: Workbook) -> bytes:
    """Liefert die Arbeitsmappe als Inhalt einer XLSX-Datei."""
    puffer = io.BytesIO()
    arbeitsmappe.save(puffer)
    return puffer.getvalue()


def kopfzeile(blatt: Worksheet, spalten: Sequence[str], breiten: Sequence[int]) -> None:
    """Schreibt die fett hinterlegte Kopfzeile, setzt Spaltenbreiten und fixiert sie."""
    blatt.append(list(spalten))
    for nr, breite in enumerate(breiten, 1):
        kopf = blatt.cell(1, nr)
        kopf.font = Font(bold=True)
        kopf.fill = KOPF_FUELLUNG
        blatt.column_dimensions[get_column_letter(nr)].width = breite
    blatt.freeze_panes = "A2"


def zeile(
    blatt: Worksheet,
    werte: Iterable[object],
    *,
    fuellung: PatternFill | None = None,
    fett: bool = False,
) -> None:
    """Hängt eine Zeile mit Zeilenumbruch an; Texte werden nie als Formel ausgewertet."""
    blatt.append([_bereinigt(w) for w in werte])
    for feld in blatt[blatt.max_row]:
        if isinstance(feld.value, str) and feld.value.startswith("="):
            feld.data_type = "s"
        feld.alignment = _UMBRUCH
        if fuellung:
            feld.fill = fuellung
        if fett:
            feld.font = Font(bold=True)


def angaben(blatt: Worksheet, werte: Iterable[tuple[str, object]]) -> None:
    """Schreibt ein Blatt mit Name und Wert je Zeile, die Namen fett."""
    blatt.column_dimensions["A"].width = 26
    blatt.column_dimensions["B"].width = 100
    for name, wert in werte:
        zeile(blatt, [name, wert])
        blatt.cell(blatt.max_row, 1).font = Font(bold=True)


def autofilter(blatt: Worksheet, spalten: int) -> None:
    """Setzt den Autofilter über alle Zeilen und die angegebene Zahl Spalten."""
    blatt.auto_filter.ref = f"A1:{get_column_letter(spalten)}{blatt.max_row}"


def _bereinigt(wert: object) -> object:
    if isinstance(wert, str):
        return _STEUERZEICHEN.sub("", wert)
    return wert
