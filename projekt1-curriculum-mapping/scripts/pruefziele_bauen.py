"""Erzeugt die Prüfziel-Liste aus der Prüfziel-Tabelle und dem IMPP-Katalog.

    python -m scripts.pruefziele_bauen <Tabelle Prüfziele.xlsx> <IMPP-Prüfziele.pdf>

Grundlage ist die Tabelle "08 QB Z2 Orale Medizin". Nummern, die Excel in
Datumswerte umgewandelt hat, werden zurückverwandelt. Namen und Nummern
werden mit dem IMPP-Gegenstandskatalog abgeglichen (pdftotext -layout).
Namen, die pdftotext abschneidet, stehen vollständig in KORREKTUR.

Ausgabe: app/daten/pruefziele_orale_medizin.json
"""

import argparse
import datetime
import difflib
import json
import os
import re
import shutil
import subprocess
import sys

import openpyxl

ZIEL = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app",
    "daten",
    "pruefziele_orale_medizin.json",
)

TEILE = {"VI": "Erkrankungen", "VIII": "Übergeordnete Kompetenzen"}

# Jahr der Tabelle, Excel hat Nummern wie "1.1." als Datum dieses Jahres gespeichert.
TABELLENJAHR = 2026

# Mehrzeilige Namen, die pdftotext -layout abschneidet, wörtlich aus dem
# Katalog ohne Querverweise.
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


def nummer(wert):
    """Liefert den Zellwert der Nummernspalte als Text.

    Excel speichert "1.1." als 1.1.2026 und "2.1.11" als 2.1.2011.
    """
    if wert is None:
        return ""
    if isinstance(wert, datetime.datetime):
        if wert.year == TABELLENJAHR:
            return f"{wert.day}.{wert.month}"
        return f"{wert.day}.{wert.month}.{wert.year % 100}"
    text = re.sub(r"\s+", "", str(wert))
    return text.rstrip(".")


def sauber(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def katalog_namen(pdf):
    """Liefert {(Teil, Nummer): Name} aus dem IMPP-Katalog ohne Querverweise."""
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        sys.exit("pdftotext wurde nicht gefunden (Paket poppler).")
    roh = subprocess.run(  # noqa: S603
        [pdftotext, "-layout", pdf, "-"], capture_output=True, text=True, check=True
    ).stdout
    namen = {}
    for zeile in roh.splitlines():
        treffer = re.match(r"^\s*(VIII|VI)\.(\d+(?:\.\d+)*)\s+(\S.*?)\s*$", zeile)
        if not treffer:
            continue
        name = re.sub(r"\s*\(\d[^()]*\)", "", treffer.group(3))
        name = re.sub(r"\s*\(\d[^()]*$", "", name).strip()
        namen.setdefault((treffer.group(1), treffer.group(2)), name)
    return namen


def aehnlich(a, b):
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def tabellenzeilen(pfad):
    """Liefert (Teil, Nummer, Name) für jede belegte Zeile der Prüfziel-Tabelle."""
    blatt = openpyxl.load_workbook(pfad).worksheets[0]
    zeilen = []
    teil = "VI"
    for zeile in blatt.iter_rows(min_row=7):
        nr, name = nummer(zeile[1].value), sauber(zeile[3].value)
        if not nr and not name:
            continue
        if nr == "VIII":
            teil = "VIII"
            continue
        zeilen.append((teil, nr, name))
    return zeilen


def eintrag_abgleichen(teil, nr, name, impp):
    """Liefert den Eintrag der Liste mit Nummer und Schreibweise nach dem IMPP-Katalog."""
    tiefe = nr.count(".") + 1
    ebene = "bereich" if tiefe == 1 else "gruppe" if tiefe == 2 else "pruefziel"
    eintrag = {"ebene": ebene, "teil": teil, "nr": nr, "name": name}

    # Passt der Name nicht zur Nummer, wird die Nummer im Katalog über den Namen
    # gesucht (Tabelle "4.12.2 Depression", Katalog 4.13.2).
    katalog = impp.get((teil, nr))
    if (
        ebene == "pruefziel"
        and (teil, nr) not in KORREKTUR
        and (not katalog or aehnlich(katalog, name) < 0.8)
    ):
        kandidaten = [
            (aehnlich(n, name), k)
            for k, n in impp.items()
            if k[0] == teil and k[1].count(".") == nr.count(".")
        ]
        wert, schluessel = max(kandidaten)
        if wert >= 0.8 and schluessel[1] != nr:
            print(f"Nummer {teil} {nr} ersetzt durch {schluessel[1]} ({name})")
            eintrag["nr_tabelle"] = nr
            eintrag["nr"] = nr = schluessel[1]
            katalog = impp[schluessel]

    neu = KORREKTUR.get((teil, nr)) or katalog
    if neu and neu != name:
        if (teil, nr) not in KORREKTUR and aehnlich(neu, name) < 0.6:
            print(f"WARNUNG {teil} {nr}: Tabelle {name!r}, Katalog {neu!r}", file=sys.stderr)
        else:
            eintrag["name"] = neu
    return eintrag


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("tabelle", help="Prüfziel-Tabelle als Excel-Datei")
    parser.add_argument("katalog", help="IMPP-Gegenstandskatalog als PDF")
    args = parser.parse_args()
    impp = katalog_namen(args.katalog)

    eintraege = [{"ebene": "teil", "teil": "VI", "nr": "VI", "name": TEILE["VI"]}]
    for teil, nr, name in tabellenzeilen(args.tabelle):
        if teil == "VIII" and eintraege[-1]["teil"] == "VI":
            eintraege.append({"ebene": "teil", "teil": "VIII", "nr": "VIII", "name": TEILE["VIII"]})
        eintraege.append(eintrag_abgleichen(teil, nr, name, impp))

    # Prüfziele mit Unterpunkten zählen nicht zur Vollständigkeit.
    for e in eintraege:
        if e["ebene"] == "pruefziel":
            e["unterpunkte"] = any(
                o["teil"] == e["teil"] and o["nr"].startswith(e["nr"] + ".") for o in eintraege
            )

    daten = {
        "schluessel": "orale-medizin",
        "titel": "Orale Medizin und systemische Aspekte (08 QB Z2)",
        "quelle": (
            "Prüfziel-Tabelle (Stand 15.06.2026), Schreibweise und "
            "Nummern nach IMPP-Gegenstandskatalog Zahnmedizin"
        ),
        "eintraege": eintraege,
    }
    os.makedirs(os.path.dirname(ZIEL), exist_ok=True)
    with open(ZIEL, "w", encoding="utf-8") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    anzahl = sum(1 for e in eintraege if e["ebene"] == "pruefziel")
    ohne_unterpunkte = sum(
        1 for e in eintraege if e["ebene"] == "pruefziel" and not e["unterpunkte"]
    )
    print(f"{anzahl} Prüfziele ({ohne_unterpunkte} ohne Unterpunkte) geschrieben nach {ZIEL}")


if __name__ == "__main__":
    main()
