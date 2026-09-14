"""Datum und Zahlen in deutscher Schreibweise, für Seiten und Excel-Export."""

import datetime


def datum(wert):
    """Liefert einen Zeitstempel der Datenbank als "TT.MM.JJJJ, HH:MM"."""
    try:
        return datetime.datetime.fromisoformat(wert).strftime("%d.%m.%Y, %H:%M")
    except (TypeError, ValueError):
        return wert or ""


def zahl(wert, stellen=None):
    """Liefert eine Zahl mit Tausenderpunkt und Dezimalkomma.

    Ohne stellen bleibt die Zahl ungerundet, sonst hat sie genau so viele
    Nachkommastellen.
    """
    text = f"{wert:,}" if stellen is None else f"{wert:,.{stellen}f}"
    return text.translate(str.maketrans(",.", ".,"))


def temperatur(wert):
    """Liefert die Temperatur ohne überflüssige Nullen, etwa "0,5"."""
    return "" if wert is None else f"{wert:g}".replace(".", ",")


def anzahl(n, einzahl, mehrzahl):
    """Liefert die Anzahl mit passendem Wort, etwa "1 Zeile" oder "3 Zeilen"."""
    return f"{n} {einzahl if n == 1 else mehrzahl}"
