"""Erzeugt die eingebaute Prüfziel-Liste aus der Prüfziel-Tabelle und dem IMPP-Katalog.

    python -m scripts.pruefziele_bauen <Tabelle Prüfziele.xlsx> <IMPP-Prüfziele.pdf>

Grundlage ist die Tabelle "08 QB Z2 Orale Medizin". Nummern, die Excel in
Datumswerte umgewandelt hat, werden zurückverwandelt. Namen und Nummern
werden mit dem IMPP-Gegenstandskatalog abgeglichen, den pruefziele.aus_text()
liest. Namen, die im Katalog über mehrere Zeilen laufen, stehen vollständig in
KORREKTUR.

Ausgabe: app/daten/pruefziele_orale_medizin.json
"""

from __future__ import annotations

import argparse
import datetime
import difflib
import json
import re
import sys
import zipfile
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import NamedTuple

import openpyxl
from openpyxl.utils.exceptions import InvalidFileException

from app import dokumente, pruefziele
from app.pruefziele import Eintrag

ZIEL = pruefziele.DATEN / pruefziele.DATEIEN[pruefziele.STANDARD]
TITEL = "Orale Medizin und systemische Aspekte (08 QB Z2)"
QUELLE = (
    "Prüfziel-Tabelle (Stand 15.06.2026), Schreibweise und "
    "Nummern nach IMPP-Gegenstandskatalog Zahnmedizin"
)

# Jahr der Tabelle, Excel hat Nummern wie "1.1." als Datum dieses Jahres gespeichert.
TABELLENJAHR = 2026
# Die Prüfziele beginnen in Zeile 7; Spalte B enthält die Nummer, Spalte D den Namen.
ERSTE_ZEILE = 7
SPALTE_NUMMER = 1
SPALTE_NAME = 3
# Ab dieser Ähnlichkeit gilt ein Katalogname als derselbe Eintrag (Nummernsuche)
# beziehungsweise als zulässige Schreibweise des Tabellennamens.
MIN_GLEICHER_EINTRAG = 0.8
MIN_SCHREIBWEISE = 0.6

# Mehrzeilige Namen aus dem Katalog, wörtlich und ohne Querverweise.
KORREKTUR = {
    ("VI", "1.2.9"): "Entwicklungsbedingte und erworbene Deformationen und Zustände des Parodonts",
    ("VI", "1.4.5"): (
        "Kieferkammatrophie, Alveolarfortsatzatrophie und weitere ungünstige "
        "anatomische Situationen (für Prothetik)"
    ),
    ("VI", "2.1.11"): (
        "Vaskulitiden der Haut und Mundschleimhaut (Kleingefäßvaskulitis / Vasculitis allergica)"
    ),
    ("VI", "2.5.3"): "Maligne odontogene Tumoren, Knochen- und Knorpeltumoren",
    ("VI", "2.6.2"): (
        "Formenkreis Rachitis, Hyperparathyreoidismus und muskuloskelettale Vitaminmangelfolgen"
    ),
    ("VI", "3.3.14"): "Traumatisch bedingte Verletzungen und Veränderungen der Mundschleimhaut",
    ("VI", "3.5.2"): "Prämaligne Veränderungen von Kopfhaut, Gesichtshaut und Mundschleimhaut",
    ("VI", "4.9.1"): (
        "Suchtverhalten, Abhängigkeit, Gebrauch und Missbrauch von Genussmitteln, "
        "Drogen und Medikamenten"
    ),
    ("VI", "4.13.1"): (
        "Persönlichkeitsstörungen (dissoziale, histrionische, paranoide, schizoide, "
        "emotional instabile Persönlichkeitsstörung)"
    ),
    ("VI", "6.1.3"): (
        "Chronisch obstruktive Lungenerkrankung (COPD), chronische Bronchitis, Lungenemphysem"
    ),
    ("VI", "6.2.4"): "Tuberkulose und Infektionen mit nicht-tuberkulösen Mykobakterien",
    ("VIII", "3.2.2.2"): (
        "Bedeutung der Zusammenarbeit von Zahnarzt / -innen, Hausarzt / -innen "
        "und Facharzt / -innen"
    ),
    ("VIII", "3.2.2.3"): (
        "Aufgabenbereiche und Expertisen der für die Patientenversorgung in der "
        "Praxis relevanten zahnärztlichen und ärztlichen Fachdisziplinen"
    ),
    ("VIII", "3.2.2.4"): (
        "Notwendigkeit der Konsultation mit behandelnden Allgemein- oder Fachärzten und -innen"
    ),
    ("VIII", "3.2.2.5"): (
        "Aufklärung von Humanmedizinerinnen und Humanmedizinern über die spezifische "
        "Situation der Patientinnen und Patienten und die potentiellen Implikationen "
        "der geplanten zahnärztlichen Maßnahmen auf deren Allgemeingesundheit"
    ),
    ("VIII", "3.2.3.3"): (
        "Einholen behandlungsrelevanter Informationen zur individuellen, "
        "biopsychosozialen Situation der behandelten Person"
    ),
    ("VIII", "3.2.3.5"): (
        "Teilhabeorientiertes Vorgehen unter Einschluss der multidisziplinären und "
        "interprofessionellen Problemerkennung und Arbeitsweise"
    ),
    ("VIII", "3.2.3.6"): (
        "Ausarbeiten eines Plans zum Teilhabemanagement (interprofessionell und mit "
        "Betroffenen und ggf. Angehörigen und gesetzlichen Vertreterinnen und Vertreter)"
    ),
    ("VIII", "3.2.3.8"): (
        "Anpassen der Zusammenstellung der an Gesundheitsförderung, Prävention, "
        "Kuration, Rehabilitation und Palliation beteiligten Gesundheitsberufe an "
        "entwicklungs-, alters- und geschlechtsspezifischen Unterschiede"
    ),
    ("VIII", "3.2.3.9"): (
        "Aspekte der interprofessionellen Gesundheitsfürsorge und Versorgung bei "
        "Kindern und Erwachsenen mit geistiger oder mehrfacher Behinderung"
    ),
    ("VIII", "4.5.2"): (
        "Erkennen und Erfassen des Gesundheitszustandes als Ganzes, des "
        "mundbezogenen Gesundheitszustandes und des Lebensstils"
    ),
    ("VIII", "4.5.2.4"): (
        "Einfluss von Mitarbeit, auch von Angehörigen / Pflegepersonal auf die Mundgesundheit"
    ),
    ("VIII", "4.5.2.5"): (
        "Auswirkungen und Einfluss von Allgemeinerkrankungen oder allgemeine "
        "medizinische Veränderungen sowie Auswirkungen der Therapie von "
        "Allgemeinerkrankungen"
    ),
    ("VIII", "4.5.2.6"): (
        "Individuelles orales Erkrankungsrisiko, Risiko für das Fortschreiten oraler Erkrankungen"
    ),
}


Schluessel = tuple[str, str]


class Tabellenzeile(NamedTuple):
    """Eine belegte Zeile der Prüfziel-Tabelle."""

    teil: str
    nr: str
    name: str


def nummer(wert: object) -> str:
    """Liefert den Zellwert der Nummernspalte als Text.

    Excel speichert "1.1." als 1.1.2026 und "2.1.11" als 2.1.2011.
    """
    if wert is None:
        return ""
    if isinstance(wert, datetime.datetime):
        if wert.year == TABELLENJAHR:
            return f"{wert.day}.{wert.month}"
        return f"{wert.day}.{wert.month}.{wert.year % 100}"
    return re.sub(r"\s+", "", str(wert)).rstrip(".")


def sauber(text: object) -> str:
    """Fasst Leerraum zusammen."""
    return re.sub(r"\s+", " ", str(text or "")).strip()


def aehnlich(a: str, b: str) -> float:
    """Zeichenweise Ähnlichkeit zweier Namen zwischen 0 und 1."""
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def katalog_namen(daten: bytes) -> dict[Schluessel, str]:
    """Liefert {(Teil, Nummer): Name} aus dem IMPP-Katalog ohne Querverweise."""
    katalog = pruefziele.aus_text(dokumente.pdf_text(daten, "IMPP-Katalog"), "IMPP-Katalog")
    return {(e["teil"], e["nr"]): e["name"] for e in katalog.eintraege if e["ebene"] != "teil"}


def tabellenzeilen(zellen: Iterable[Sequence[object]]) -> list[Tabellenzeile]:
    """Liefert die belegten Zeilen der Prüfziel-Tabelle; "VIII" beginnt den zweiten Teil."""
    zeilen = []
    teil = "VI"
    for zeile in zellen:
        nr, name = nummer(zeile[SPALTE_NUMMER]), sauber(zeile[SPALTE_NAME])
        if nr == "VIII":
            teil = nr
        elif nr or name:
            zeilen.append(Tabellenzeile(teil, nr, name))
    return zeilen


def tabelle_lesen(pfad: Path) -> list[Tabellenzeile]:
    """Liest die Prüfziel-Tabelle aus der ersten Tabelle der Excel-Datei."""
    mappe = openpyxl.load_workbook(pfad, read_only=True)
    try:
        werte = mappe.worksheets[0].iter_rows(min_row=ERSTE_ZEILE, values_only=True)
        return tabellenzeilen(werte)
    finally:
        mappe.close()


def nummer_nach_name(zeile: Tabellenzeile, impp: dict[Schluessel, str]) -> str:
    """Sucht die Nummer eines Prüfziels im Katalog über den Namen.

    Nötig, wenn die Tabelle eine veraltete Nummer nennt, etwa "4.12.2 Depression"
    statt 4.13.2. Ohne eindeutigen Treffer bleibt die Nummer der Tabelle.
    """
    tiefe = zeile.nr.count(".")
    kandidaten = [
        (aehnlich(name, zeile.name), nr)
        for (teil, nr), name in impp.items()
        if teil == zeile.teil and nr.count(".") == tiefe
    ]
    wert, nr = max(kandidaten, default=(0.0, zeile.nr))
    return nr if wert >= MIN_GLEICHER_EINTRAG else zeile.nr


def eintrag_abgleichen(zeile: Tabellenzeile, impp: dict[Schluessel, str]) -> Eintrag:
    """Liefert den Eintrag der Liste mit Nummer und Schreibweise nach dem IMPP-Katalog."""
    ebene = pruefziele.EBENE_NACH_TIEFE.get(zeile.nr.count(".") + 1, "pruefziel")
    eintrag: Eintrag = {"ebene": ebene, "teil": zeile.teil, "nr": zeile.nr, "name": zeile.name}
    if ebene == "pruefziel":
        nr = nummer_abgleichen(zeile, impp)
        if nr != zeile.nr:
            print(f"Nummer {zeile.teil} {zeile.nr} ersetzt durch {nr} ({zeile.name})")
            eintrag.update(nr_tabelle=zeile.nr, nr=nr)
    eintrag["name"] = schreibweise(zeile, eintrag["nr"], impp)
    return eintrag


def nummer_abgleichen(zeile: Tabellenzeile, impp: dict[Schluessel, str]) -> str:
    """Nummer des Prüfziels im Katalog.

    Weicht der Name unter der Nummer der Tabelle zu stark ab, gilt die Nummer
    des Katalogeintrags mit dem ähnlichsten Namen. Nummern aus KORREKTUR
    bleiben unverändert.
    """
    schluessel = (zeile.teil, zeile.nr)
    if schluessel in KORREKTUR or aehnlich(impp.get(schluessel, ""), zeile.name) >= (
        MIN_GLEICHER_EINTRAG
    ):
        return zeile.nr
    return nummer_nach_name(zeile, impp)


def schreibweise(zeile: Tabellenzeile, nr: str, impp: dict[Schluessel, str]) -> str:
    """Name nach KORREKTUR oder Katalog; bei zu großer Abweichung bleibt der Name der Tabelle."""
    korrektur = KORREKTUR.get((zeile.teil, nr))
    if korrektur:
        return korrektur
    katalog = impp.get((zeile.teil, nr))
    if not katalog or katalog == zeile.name:
        return zeile.name
    if aehnlich(katalog, zeile.name) >= MIN_SCHREIBWEISE:
        return katalog
    print(
        f"WARNUNG {zeile.teil} {nr}: Tabelle {zeile.name!r}, Katalog {katalog!r}",
        file=sys.stderr,
    )
    return zeile.name


def liste_bauen(zeilen: Iterable[Tabellenzeile], impp: dict[Schluessel, str]) -> list[Eintrag]:
    """Liefert die Einträge der Liste mit Teilen und markiert Prüfziele mit Unterpunkten."""
    eintraege: list[Eintrag] = []
    for zeile in zeilen:
        if not eintraege or eintraege[-1]["teil"] != zeile.teil:
            name = pruefziele.TEILE[zeile.teil]
            eintraege.append({"ebene": "teil", "teil": zeile.teil, "nr": zeile.teil, "name": name})
        eintraege.append(eintrag_abgleichen(zeile, impp))
    # Prüfziele mit Unterpunkten zählen nicht zur Vollständigkeit.
    for e in eintraege:
        if e["ebene"] == "pruefziel":
            e["unterpunkte"] = any(
                o["teil"] == e["teil"] and o["nr"].startswith(f"{e['nr']}.") for o in eintraege
            )
    return eintraege


def speichern(eintraege: list[Eintrag], ziel: Path) -> None:
    """Schreibt die Liste im Format von pruefziele.liste()."""
    daten = {
        "schluessel": pruefziele.STANDARD,
        "titel": TITEL,
        "quelle": QUELLE,
        "eintraege": eintraege,
    }
    ziel.write_text(json.dumps(daten, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Baut die Liste und meldet die Anzahl der Prüfziele."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("tabelle", type=Path, help="Prüfziel-Tabelle als Excel-Datei")
    parser.add_argument("katalog", type=Path, help="IMPP-Gegenstandskatalog als PDF")
    parser.add_argument("--ziel", type=Path, default=ZIEL, help="Ausgabedatei (JSON)")
    args = parser.parse_args(argv)
    try:
        impp = katalog_namen(args.katalog.read_bytes())
        eintraege = liste_bauen(tabelle_lesen(args.tabelle), impp)
        speichern(eintraege, args.ziel)
    except (OSError, zipfile.BadZipFile, InvalidFileException, dokumente.DokumentFehler) as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1
    pruefziele_gesamt = [e for e in eintraege if e["ebene"] == "pruefziel"]
    ohne_unterpunkte = sum(1 for e in pruefziele_gesamt if not e["unterpunkte"])
    print(
        f"{len(pruefziele_gesamt)} Prüfziele ({ohne_unterpunkte} ohne Unterpunkte) "
        f"geschrieben nach {args.ziel}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
