"""Export eines Vorlesungsabgleichs als Excel-Datei.

Das Blatt "Folien" enthält die Ziele je Folie, das zweite Blatt die Folien je
Ziel.
"""

from __future__ import annotations

import sqlite3

from openpyxl.worksheet.worksheet import Worksheet

from .. import excel, formate
from ..config import KiEinstellungen
from .auswertung import Ergebnis, Folie
from .katalog import ZIELARTEN, Katalog

BLATT = "Folien"
_FOLIEN_BREITEN = (8, 40, 18, 60, 70, 30)


def dateiname(abgleich: sqlite3.Row) -> str:
    """Name der Excel-Datei eines Abgleichs."""
    return excel.dateiname("Vorlesungsabgleich", abgleich["titel"])


def xlsx(abgleich: sqlite3.Row, ergebnis: Ergebnis, ziele: Katalog, ki: KiEinstellungen) -> bytes:
    """Liefert die Excel-Datei mit den Blättern Folien, Nach Lernzielen oder Prüfzielen, Angaben."""
    zielart = ZIELARTEN[abgleich["ziel"]]
    mappe, blatt = excel.mappe()
    blatt.title = BLATT
    spalten = (
        "Folie",
        "Überschrift",
        zielart.name,
        "Bildbeschreibung",
        "Text der Folie",
        "Hinweis",
    )
    excel.kopfzeile(blatt, spalten, _FOLIEN_BREITEN)
    for folie in ergebnis.folien:
        excel.zeile(blatt, _folienzeile(folie))
    _je_ziel(mappe.create_sheet(f"Nach {zielart.dativ}"), ergebnis, ziele)
    excel.angaben(mappe.create_sheet("Angaben"), _angaben(abgleich, ergebnis, ziele, ki))
    return excel.als_bytes(mappe)


def _folienzeile(folie: Folie) -> list[object]:
    if folie.offen:
        hinweis = "noch nicht bearbeitet"
    elif folie.unbekannt:
        hinweis = "nicht in der Liste: " + ", ".join(folie.unbekannt)
    else:
        hinweis = ""
    angaben = [e.anzeige for e in folie.ziele] + folie.unbekannt
    return [folie.nr, folie.titel, "\n".join(angaben), folie.bild or "", folie.text, hinweis]


def _je_ziel(blatt: Worksheet, ergebnis: Ergebnis, ziele: Katalog) -> None:
    zielart = ZIELARTEN[ziele.art]
    name = "Wortlaut" if ziele.art == "lernziele" else "Name"
    excel.kopfzeile(blatt, (zielart.einzahl, name, "Anzahl Folien", "Folien"), (14, 80, 14, 40))
    for z in ergebnis.zeilen:
        e = z.eintrag
        nummern = ", ".join(map(str, z.folien))
        if e.art == "ziel":
            excel.zeile(blatt, [e.anzeige, e.name, len(z.folien), nummern])
        else:
            werte = [e.anzeige, e.name, len(z.folien) or "", nummern]
            excel.zeile(blatt, werte, fuellung=excel.GRUPPE_FUELLUNG[e.art], fett=True)
    for angabe, folien in ergebnis.unbekannt.items():
        excel.zeile(blatt, [angabe, "nicht in der Liste", len(folien), ", ".join(map(str, folien))])


def _angaben(
    abgleich: sqlite3.Row, ergebnis: Ergebnis, ziele: Katalog, ki: KiEinstellungen
) -> list[tuple[str, object]]:
    zielart = ZIELARTEN[abgleich["ziel"]]
    temperatur = abgleich["temperatur"]
    bildmodell = abgleich["bildmodell"]
    return [
        ("Titel", abgleich["titel"]),
        ("Abgleich mit", ziele.titel),
        ("Vorlesung", abgleich["vorlesung_name"]),
        ("Modell", ki.modell_name(abgleich["modell"])),
        ("Bildmodell", ki.modell_name(bildmodell) if bildmodell else ""),
        ("Temperatur", "" if temperatur is None else temperatur),
        ("Erstellt", formate.erstellt(abgleich)),
        ("Folien", ergebnis.gesamt),
        ("Folien bearbeitet", ergebnis.bearbeitet),
        ("Folien mit Zuordnung", ergebnis.mit_zuordnung),
        (f"{zielart.name} in der Liste", ergebnis.zaehlend),
        (f"{zielart.name} mit Folie", ergebnis.abgedeckt),
        ("Prompt", abgleich["prompt"] or ""),
    ]
