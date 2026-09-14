"""Import von Ergebnis-Excel-Dateien.

Jedes Blatt entspricht einem Durchlauf. Die Zellen einer Zeile werden zu einer
Antwortzeile im Format des Prompts verbunden und mit derselben Funktion
gelesen wie eine Antwort des Modells.

Enthält ein Blatt eine Kopfzeile mit Prüfziel und Abdeckung, etwa aus dem
Export der App, zählen nur die benannten Spalten. Sonst beginnt die
Antwortzeile in der Spalte mit den Prüfzielen.
"""

import datetime
import io
import re
import zipfile

import openpyxl

from . import ki_dienst, zuordnung


class ExcelFehler(ValueError):
    """Die Datei ist keine lesbare Ergebnis-Excel."""


def zelle(wert):
    if wert is None:
        return ""
    if isinstance(wert, datetime.datetime):
        # Excel wandelt Nummern wie "4.5.2" in das Datum 4.5.2002 um.
        return f"{wert.day}.{wert.month}.{wert.year % 100}"
    if isinstance(wert, float) and wert.is_integer():
        return str(int(wert))
    return re.sub(r"\s+", " ", str(wert)).strip()


def blaetter(daten):
    """Liefert (Blattname, Antworttext, Zeilenzahl) für alle Blätter mit Zuordnungen."""
    try:
        mappe = openpyxl.load_workbook(io.BytesIO(daten), read_only=True, data_only=True)
    except (zipfile.BadZipFile, OSError, KeyError, ValueError) as exc:
        raise ExcelFehler("Die Datei ist keine lesbare Excel-Datei (.xlsx).") from exc
    ergebnis = []
    for blatt in mappe.worksheets:
        zeilen = [[zelle(w) for w in reihe] for reihe in blatt.iter_rows(values_only=True)]
        zeilen = [z for z in zeilen if any(z)]
        if not zeilen:
            continue
        spalten = _kopf_spalten(zeilen)
        if spalten:
            text = "\n".join(filter(None, (_aus_spalten(z, spalten) for z in zeilen)))
        else:
            start = _pruefziel_spalte(zeilen)
            text = "\n".join(_als_antwortzeile(z[start:]) for z in zeilen)
        gelesen, _ = zuordnung.lesen(text)
        if gelesen:
            ergebnis.append((blatt.title.strip(), text, len(gelesen)))
    mappe.close()
    if not ergebnis:
        raise ExcelFehler(
            "In der Excel-Datei steht keine Zuordnung. Erwartet werden Zeilen mit "
            "Prüfziel, Abdeckung, Begründung und Lernziel-ID."
        )
    return ergebnis


def temperatur_aus_name(name):
    treffer = re.search(r"(\d+(?:[.,]\d+)?)", name or "")
    if not treffer:
        return None
    wert = float(treffer.group(1).replace(",", "."))
    return wert if 0 <= wert <= ki_dienst.MAX_TEMPERATUR else None


_KOPF = {
    "teil": ("teil",),
    "pruefziel": ("prüfziel", "pruefziel"),
    "abdeckung": ("abdeckung",),
    "begruendung": ("begründung", "begruendung"),
    "lernziele": ("lernziel",),
}


def _kopf_spalten(zeilen):
    """Sucht in den ersten Zeilen eine Kopfzeile und liefert {Feld: Spaltenindex}.

    Fehlen die Spalten Prüfziel oder Abdeckung, ist das Ergebnis None.
    """
    for z in zeilen[:5]:
        spalten = {}
        for i, wert in enumerate(z):
            w = wert.replace("*", "").strip().lower()
            for feld, anfaenge in _KOPF.items():
                if feld not in spalten and w.startswith(anfaenge):
                    spalten[feld] = i
                    break
        if "pruefziel" in spalten and "abdeckung" in spalten:
            return spalten
    return None


def _aus_spalten(z, spalten):
    """Setzt eine Antwortzeile aus den benannten Spalten zusammen.

    Zeilen, die nur die Prüfziel-Spalte füllen, bleiben ohne Trennzeichen und
    gelten beim Lesen als Überschrift.
    """

    def wert(feld):
        i = spalten.get(feld)
        return z[i] if i is not None and i < len(z) else ""

    pruefziel = wert("pruefziel")
    teil = wert("teil").upper()
    if teil in ("VI", "VIII") and pruefziel and not pruefziel.upper().startswith("VI"):
        pruefziel = f"{teil} {pruefziel}"
    rest = [wert("abdeckung"), wert("begruendung"), wert("lernziele")]
    if not any(r.strip() for r in rest):
        return pruefziel
    return ";".join(x.replace(";", ",") for x in (pruefziel, *rest))


def _pruefziel_spalte(zeilen):
    """Liefert den Index der Spalte, in der die meisten Zeilen mit einem Prüfziel beginnen."""
    zaehler = {}
    for z in zeilen:
        for i, wert in enumerate(z):
            if zuordnung.beginnt_mit_pruefziel(wert):
                zaehler[i] = zaehler.get(i, 0) + 1
                break
    return max(zaehler, key=zaehler.get) if zaehler else 0


def _als_antwortzeile(zellen):
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
