"""Prüfziel-Listen aus app/daten/pruefziele_*.json.

Eine Liste enthält Teile (VI, VIII), Bereiche, Gruppen und Prüfziele in der
Reihenfolge des Katalogs. Das Modell erhält sie über text_fuer_modell(),
finde() ordnet gelesene Antwortzeilen einem Prüfziel zu. Die JSON-Datei
erzeugt scripts/pruefziele_bauen.py.
"""

import difflib
import functools
import json
import os
import re

DATEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "daten")
STANDARD = "orale-medizin"
DATEIEN = {"orale-medizin": "pruefziele_orale_medizin.json"}

# Mindestähnlichkeit der Namen bei passender und bei fehlender Nummer
MIN_AEHNLICHKEIT_MIT_NUMMER = 0.45
MIN_AEHNLICHKEIT_OHNE_NUMMER = 0.8

_WORT = re.compile(r"[a-zäöüß]{4,}")


def aehnlichkeit(a, b):
    """Liefert die Ähnlichkeit zweier Namen zwischen 0 und 1.

    Maßgeblich ist der höhere Wert aus Zeichenvergleich und Wortüberdeckung,
    so werden auch gekürzte Namen erkannt.
    """
    a, b = (a or "").lower(), (b or "").lower()
    if not a or not b:
        return 0.0
    zeichen = difflib.SequenceMatcher(None, a, b).ratio()
    wa, wb = set(_WORT.findall(a)), set(_WORT.findall(b))
    kurz, lang = (wa, wb) if len(wa) <= len(wb) else (wb, wa)
    woerter = len(kurz & lang) / len(kurz) if kurz else 0.0
    return max(zeichen, woerter * 0.95)


class Liste:
    def __init__(self, daten):
        self.schluessel = daten["schluessel"]
        self.titel = daten["titel"]
        self.quelle = daten["quelle"]
        self.eintraege = daten["eintraege"]
        for e in self.eintraege:
            e["schluessel"] = f"{e['teil']}-{e['nr']}"
        self.bereiche = [e for e in self.eintraege if e["ebene"] == "bereich"]
        self.pruefziele = [e for e in self.eintraege if e["ebene"] == "pruefziel"]
        # Prüfziele mit Unterpunkten zählen nicht zur Vollständigkeit.
        self.zaehlend = [e for e in self.pruefziele if not e.get("unterpunkte")]

    def text_fuer_modell(self):
        """Liefert die Liste als Text mit einer Zeile je Eintrag.

        Vor Teilen und Bereichen steht eine Leerzeile.
        """
        zeilen = []
        for e in self.eintraege:
            if e["ebene"] in ("teil", "bereich"):
                zeilen.append(f"\n{e['nr']} {e['name']}")
            else:
                zeilen.append(f"{e['nr']} {e['name']}")
        return "\n".join(zeilen).strip()

    def finde(self, teil, nr, name):
        """Sucht das Prüfziel zu einer gelesenen Zeile, sonst None.

        Vorrang hat die Nummer, auch die abweichende Nummer der Prüfziel-Tabelle
        (nr_tabelle). Der Name muss dann nur grob passen. Ohne passende Nummer
        entscheidet ein sehr ähnlicher Name.
        """
        kandidaten = [
            e
            for e in self.pruefziele
            if nr in (e["nr"], e.get("nr_tabelle")) and teil in (None, e["teil"])
        ]
        if kandidaten:
            wert, bester = max(
                ((aehnlichkeit(e["name"], name), e) for e in kandidaten),
                key=lambda paar: paar[0],
            )
            if wert >= MIN_AEHNLICHKEIT_MIT_NUMMER:
                return bester
        pool = [e for e in self.pruefziele if teil in (None, e["teil"])]
        if not pool or not name:
            return None
        wert, bester = max(
            ((aehnlichkeit(e["name"], name), e) for e in pool), key=lambda paar: paar[0]
        )
        return bester if wert >= MIN_AEHNLICHKEIT_OHNE_NUMMER else None


@functools.cache
def liste(schluessel=STANDARD):
    datei = DATEIEN.get(schluessel)
    if not datei:
        raise KeyError(f"Unbekannte Prüfziel-Liste: {schluessel}")
    with open(os.path.join(DATEN, datei), encoding="utf-8") as fh:
        return Liste(json.load(fh))


def auswahl():
    """Liefert (Schlüssel, Titel) aller Listen für Auswahlfelder."""
    return [(s, liste(s).titel) for s in DATEIEN]
