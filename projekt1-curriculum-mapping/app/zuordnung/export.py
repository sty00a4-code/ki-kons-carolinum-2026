"""Export einer Zuordnung als Excel-Datei.

Das Blatt "Zuordnung" enthält Prüfziel, Abdeckung, Begründung und Lernziel-ID
sowie Teil, Wortlaut der Lernziele und Hinweise. Die Datei lässt sich auch
nach manuellen Korrekturen wieder übernehmen (siehe excel_import).
"""

from __future__ import annotations

import sqlite3

from openpyxl.worksheet.worksheet import Worksheet

from .. import excel, formate
from ..config import KiEinstellungen
from ..pruefziele import Liste
from .antwort import ABGEDECKT, NICHT, TEILWEISE, Zeile
from .auswertung import Ergebnis, Tabellenzeile

ABDECKUNG = {ABGEDECKT: "X", TEILWEISE: "teilweise", NICHT: ""}

_SPALTEN = (
    "Teil",
    "Prüfziel",
    "Abdeckung",
    "Begründung",
    "Lernziel-ID (Kapitel)",
    "Wortlaut der Lernziele",
    "Hinweis",
)
_BREITEN = (7, 48, 11, 70, 22, 70, 30)


def dateiname(zuordnung: sqlite3.Row) -> str:
    """Name der Excel-Datei einer Zuordnung."""
    return excel.dateiname("Zuordnung", zuordnung["titel"])


def xlsx(zuordnung: sqlite3.Row, ergebnis: Ergebnis, liste: Liste, ki: KiEinstellungen) -> bytes:
    """Liefert die Excel-Datei mit den Blättern Zuordnung, Nach Lernzielen und Angaben."""
    mappe, blatt = excel.mappe()
    blatt.title = "Zuordnung"
    excel.kopfzeile(blatt, _SPALTEN, _BREITEN)
    for tabellenzeile in ergebnis.tabelle:
        _tabellenzeile(blatt, tabellenzeile, ergebnis)
    excel.autofilter(blatt, len(_SPALTEN))
    _lernziele(mappe.create_sheet("Nach Lernzielen"), ergebnis)
    excel.angaben(mappe.create_sheet("Angaben"), _angaben(zuordnung, ergebnis, liste, ki))
    return excel.als_bytes(mappe)


def _tabellenzeile(blatt: Worksheet, t: Tabellenzeile, ergebnis: Ergebnis) -> None:
    e = t.eintrag or {}
    if t.zeile is not None:
        excel.zeile(blatt, _antwortzeile(t.zeile, ergebnis))
    elif t.art == "fehlt":
        hinweis = "fehlt in der Antwort des Modells"
        excel.zeile(blatt, [e["teil"], f"{e['nr']} {e['name']}", "", "", "", "", hinweis])
    else:
        name = e["name"] if t.art == "teil" else f"{e['nr']} {e['name']}"
        fuellung = excel.GRUPPE_FUELLUNG[t.art]
        excel.zeile(blatt, [e.get("teil") or "", name], fuellung=fuellung, fett=True)


def _antwortzeile(z: Zeile, ergebnis: Ergebnis) -> list[object]:
    e = z.eintrag
    wortlaut = "\n".join(
        f"{lid}: {ergebnis.lernziel_texte[lid]}"
        for lid in z.lernziele
        if lid in ergebnis.lernziel_texte
    )
    hinweise = [] if e else ["nicht in der Prüfziel-Liste"]
    unbekannt = [lid for lid in z.lernziele if lid in ergebnis.unbekannte_ids]
    if unbekannt:
        hinweise.append("nicht im Lernziel-Dokument: " + ", ".join(unbekannt))
    return [
        e["teil"] if e else (z.teil or ""),
        f"{e['nr']} {e['name']}" if e else f"{z.nr} {z.name}",
        ABDECKUNG[z.stufe],
        z.begruendung,
        ", ".join(z.lernziele),
        wortlaut,
        "; ".join(hinweise),
    ]


def _lernziele(blatt: Worksheet, ergebnis: Ergebnis) -> None:
    excel.kopfzeile(
        blatt, ("Lernziel-ID", "Wortlaut", "Anzahl Prüfziele", "Prüfziele"), (14, 70, 10, 70)
    )
    for lz in ergebnis.lernziele:
        pruefziele = "\n".join(pruefziel_text(z) for z in lz.zeilen)
        hinweis = " (kommt im Lernziel-Dokument nicht vor)" if lz.unbekannt else ""
        excel.zeile(blatt, [lz.id, lz.text + hinweis, lz.anzahl, pruefziele])


def pruefziel_text(z: Zeile) -> str:
    """Liefert Teil, Nummer und Name, bei zugeordneten Zeilen aus der Prüfziel-Liste."""
    if z.eintrag:
        return f"{z.eintrag['teil']} {z.eintrag['nr']} {z.eintrag['name']}"
    return f"{z.teil or ''} {z.nr} {z.name}".strip()


def _angaben(
    zuordnung: sqlite3.Row, ergebnis: Ergebnis, liste: Liste, ki: KiEinstellungen
) -> list[tuple[str, object]]:
    temperatur = zuordnung["temperatur"]
    return [
        ("Titel", zuordnung["titel"]),
        ("Kategorie", zuordnung["kategorie"]),
        ("Prüfziel-Liste", liste.titel),
        ("Modell", ki.modell_name(zuordnung["modell"])),
        ("Temperatur", "" if temperatur is None else temperatur),
        ("Quelle", formate.quelle(zuordnung)),
        ("Vorlesung", zuordnung["vorlesung_name"] or ""),
        ("Lernziele", zuordnung["lernziele_name"] or ""),
        ("Erstellt", formate.erstellt(zuordnung)),
        ("Zeilen in der Antwort", len(ergebnis.zeilen)),
        ("Abgedeckt (X)", ergebnis.abgedeckt),
        ("Teilweise abgedeckt", ergebnis.teilweise),
        ("Nicht abgedeckt", ergebnis.nicht),
        ("Prüfziele ohne Zeile", len(ergebnis.fehlend)),
        ("Prompt", zuordnung["prompt"] or ""),
    ]
