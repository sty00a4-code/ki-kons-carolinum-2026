"""Bausteine für das Schreiben von Excel-Dateien."""

from __future__ import annotations

import io
import re
from collections.abc import Iterable, Sequence

from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.workbook.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

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


def dateiname(praefix: str, titel: str) -> str:
    """Liefert einen Dateinamen wie "Vorlesungsabgleich Titel.xlsx" ohne problematische Zeichen."""
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


def _bereinigt(wert: object) -> object:
    if isinstance(wert, str):
        return _STEUERZEICHEN.sub("", wert)
    return wert
