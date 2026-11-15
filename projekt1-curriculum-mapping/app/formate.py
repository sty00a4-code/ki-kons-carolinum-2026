"""Datum, Zahlen und Angaben zu Ergebnissen in deutscher Schreibweise.

Genutzt von den Seiten und vom Excel-Export.
"""

from __future__ import annotations

import datetime
import sqlite3

_DEUTSCH = str.maketrans(",.", ".,")


def datum(wert: str | None) -> str:
    """Liefert einen Zeitstempel der Datenbank als "TT.MM.JJJJ, HH:MM"."""
    try:
        return datetime.datetime.fromisoformat(wert or "").strftime("%d.%m.%Y, %H:%M")
    except ValueError:
        return wert or ""


def zahl(wert: float, stellen: int | None = None) -> str:
    """Liefert eine Zahl mit Tausenderpunkt und Dezimalkomma.

    Ohne stellen bleibt die Zahl ungerundet, sonst hat sie genau so viele
    Nachkommastellen.
    """
    text = f"{wert:,}" if stellen is None else f"{wert:,.{stellen}f}"
    return text.translate(_DEUTSCH)


def temperatur(wert: float | None) -> str:
    """Liefert die Temperatur ohne überflüssige Nullen, etwa "0,5"."""
    return "" if wert is None else f"{wert:g}".replace(".", ",")


def anzahl(n: int, einzahl: str, mehrzahl: str) -> str:
    """Liefert die Anzahl mit passendem Wort, etwa "1 Zeile" oder "3 Zeilen"."""
    return f"{n} {einzahl if n == 1 else mehrzahl}"


def quelle(datensatz: sqlite3.Row) -> str:
    """Herkunft eines Ergebnisses: Durchlauf in der App oder übernommene Datei."""
    if datensatz["quelle"] == "ki":
        return "KI-Durchlauf in der App"
    return str(datensatz["quelle_hinweis"] or "")


def erstellt(datensatz: sqlite3.Row) -> str:
    """Zeitpunkt der Erstellung und, falls bekannt, wer das Ergebnis angelegt hat."""
    text = datum(datensatz["erstellt_am"])
    if datensatz["erstellt_von"]:
        text += f" von {datensatz['erstellt_von']}"
    return text
