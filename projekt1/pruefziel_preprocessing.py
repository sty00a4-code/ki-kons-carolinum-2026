"""Liest die Prüfziele aus der Tabelle einer PDF-Datei und schreibt sie als JSON.

Aufruf im Ordner projekt1:

    python pruefziel_preprocessing.py

Der Aufruf liest assets/Prüfziele/PrüfzieleTabelle.pdf und schreibt
pruefziele.json. Der Aufbau folgt lernziele_umstrukturiert.json: Jeder Eintrag
hat "id" und "beschreibung", untergeordnete Einträge stehen in "teilziele".
"""

import json
import os
import re

import pdfplumber

PDF = "assets/Prüfziele/PrüfzieleTabelle.pdf"
JSON = "pruefziele.json"

# Nummer eines Eintrags wie "1", "1.1" oder "2.5.4.1"
NUMMER = re.compile(r"\d+(\.\d+)*")
# Römische Zahl eines Teils wie "VIII"
TEIL = re.compile(r"[IVX]+")


def zeilen_lesen(input_pdf):
    """Liefert die Tabellenzeilen einer PDF, je Zeile die gefüllten Zellen."""
    zeilen = []
    with pdfplumber.open(input_pdf) as pdf:
        for page in pdf.pages:
            for tabelle in page.extract_tables():
                for zeile in tabelle:
                    # Zeilenumbrüche innerhalb einer Zelle werden zu Leerzeichen
                    zellen = [" ".join((zelle or "").split()) for zelle in zeile]
                    zellen = [zelle for zelle in zellen if zelle]
                    if zellen:
                        zeilen.append(zellen)
    return zeilen


def pruefziele_lesen(input_pdf):
    """Liest die Prüfziele einer PDF als Baum.

    In der Tabelle steht die Nummer in der ersten und der Name in der zweiten
    gefüllten Spalte. Die Tiefe der Nummer bestimmt die Ebene: "1" ist ein
    Bereich, "1.1" eine Gruppe, "1.1.1" ein Prüfziel. Nach einer Zeile mit
    römischer Zahl wie "VIII" beginnt ein neuer Teil, dessen Nummern die Zahl
    als Vorsatz erhalten ("VIII.2.5.4"), damit jede Nummer nur einmal vorkommt.
    """
    zeilen = zeilen_lesen(input_pdf)
    pruefziele = []
    # Übergeordnete Einträge des aktuellen Eintrags, je mit ihrer Tiefe
    offen = []
    teil = ""
    for zellen in zeilen:
        if len(zellen) == 1:
            continue
        nummer = zellen[0].replace(" ", "").rstrip(".")
        if TEIL.fullmatch(nummer):
            teil, tiefe, kennung = nummer + ".", 0, nummer
        elif NUMMER.fullmatch(nummer):
            tiefe, kennung = nummer.count(".") + 1, teil + nummer
        else:
            continue
        eintrag = {"id": kennung, "beschreibung": zellen[1]}
        while offen and offen[-1][0] >= tiefe:
            offen.pop()
        if offen:
            offen[-1][1].setdefault("teilziele", []).append(eintrag)
        else:
            pruefziele.append(eintrag)
        offen.append((tiefe, eintrag))
    return {
        "kapitel": " ".join(zeilen[0]) if zeilen else "",
        "quelle": os.path.basename(input_pdf),
        "prüfziele": pruefziele,
    }


def zaehlen(eintraege):
    """Zählt die Einträge eines Baums samt ihrer Teilziele."""
    return sum(1 + zaehlen(eintrag.get("teilziele", [])) for eintrag in eintraege)


def pruefziele_speichern(input_pdf=PDF, output_json=JSON):
    """Schreibt die Prüfziele einer PDF als JSON-Datei und liefert ihre Anzahl.

    Enthält die PDF keine Prüfziele, bleibt die JSON-Datei unverändert.
    """
    daten = pruefziele_lesen(input_pdf)
    anzahl = zaehlen(daten["prüfziele"])
    if anzahl:
        with open(output_json, "w", encoding="utf-8") as datei:
            json.dump(daten, datei, ensure_ascii=False, indent=2)
    return anzahl


if __name__ == "__main__":
    gespeichert = pruefziele_speichern()
    print(f"Erfolgreich! {gespeichert} Prüfziele wurden nach '{JSON}' gespeichert.")
