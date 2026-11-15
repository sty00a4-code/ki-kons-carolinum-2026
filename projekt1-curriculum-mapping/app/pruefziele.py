"""Prüfziel-Listen aus app/daten/pruefziele_*.json.

Eine Liste enthält Teile (VI, VIII), Bereiche, Gruppen und Prüfziele in der
Reihenfolge des Katalogs. Das Modell erhält sie über text_fuer_modell(),
finde() ordnet gelesene Antwortzeilen einem Prüfziel zu. Die JSON-Datei
erzeugt scripts/pruefziele_bauen.py. aus_text() liest eine Liste aus dem Text
einer hochgeladenen Datei, etwa einem Kapitel des IMPP-Gegenstandskatalogs.
"""

from __future__ import annotations

import difflib
import functools
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DATEN = Path(__file__).with_name("daten")
STANDARD = "orale-medizin"
DATEIEN = {"orale-medizin": "pruefziele_orale_medizin.json"}
TEILE = {"VI": "Erkrankungen", "VIII": "Übergeordnete Kompetenzen"}
# Schlüssel einer Liste aus einer hochgeladenen Datei
AUS_DATEI = "datei"
# Kürzere Namen gelten beim Lesen einer Datei nicht als Prüfziel.
MIN_NAME = 3
# Ebene nach der Anzahl der Zahlen in der Nummer, ab drei Zahlen ein Prüfziel
EBENE_NACH_TIEFE = {1: "bereich", 2: "gruppe"}

# Mindestähnlichkeit der Namen bei passender und bei fehlender Nummer
MIN_AEHNLICHKEIT_MIT_NUMMER = 0.45
MIN_AEHNLICHKEIT_OHNE_NUMMER = 0.8
# Gewicht der Wortüberdeckung gegenüber dem Zeichenvergleich
WORTGEWICHT = 0.95

# Ein Eintrag der Liste mit ebene, teil, nr, name und optional nr_tabelle, unterpunkte
Eintrag = dict[str, Any]

_WORT = re.compile(r"[a-zäöüß]{4,}")
# "VI.1.1.1 Karies (2.1.1)" oder "1.1.1 Karies"; der Name beginnt nicht mit einer Ziffer.
_ZEILE = re.compile(r"^(?:(VIII|VI)\s*\.?\s*)?(\d{1,2}(?:\.\d{1,2}){0,3})\.?\s+([^\d\s(].*?)\s*$")
# "VI Erkrankungen" als Überschrift eines Teils
_TEIL_ZEILE = re.compile(r"^(VIII|VI)\.?\s+([^\d\s.].*?)\s*$")
# Querverweise in Klammern, Punktleisten und Seitenzahlen im Inhaltsverzeichnis
_ANHANG = re.compile(r"\s*\(\d[^()]*(?:\)|$)|\s*\.{3,}\s*\d*\s*$")


def aehnlichkeit(a: str | None, b: str | None) -> float:
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
    return max(zeichen, woerter * WORTGEWICHT)


def aehnlichster(eintraege: list[Eintrag], name: str) -> tuple[float, Eintrag | None]:
    """Liefert (Ähnlichkeit, Eintrag) des Eintrags, dessen Name name am nächsten kommt."""
    return max(
        ((aehnlichkeit(e["name"], name), e) for e in eintraege),
        key=lambda paar: paar[0],
        default=(0.0, None),
    )


@dataclass
class Liste:
    """Eine Prüfziel-Liste in der Reihenfolge des Katalogs."""

    schluessel: str
    titel: str
    quelle: str
    eintraege: list[Eintrag]
    bereiche: list[Eintrag] = field(init=False)
    pruefziele: list[Eintrag] = field(init=False)
    zaehlend: list[Eintrag] = field(init=False)

    def __post_init__(self) -> None:
        for e in self.eintraege:
            e["schluessel"] = f"{e['teil']}-{e['nr']}"
        self.bereiche = [e for e in self.eintraege if e["ebene"] == "bereich"]
        self.pruefziele = [e for e in self.eintraege if e["ebene"] == "pruefziel"]
        # Prüfziele mit Unterpunkten zählen nicht zur Vollständigkeit.
        self.zaehlend = [e for e in self.pruefziele if not e.get("unterpunkte")]

    def text_fuer_modell(self) -> str:
        """Liefert die Liste als Text mit einer Zeile je Eintrag.

        Vor Teilen und Bereichen steht eine Leerzeile.
        """
        zeilen = []
        for e in self.eintraege:
            abstand = "\n" if e["ebene"] in ("teil", "bereich") else ""
            zeilen.append(f"{abstand}{e['nr']} {e['name']}")
        return "\n".join(zeilen).strip()

    def finde(self, teil: str | None, nr: str, name: str) -> Eintrag | None:
        """Sucht das Prüfziel zu einer gelesenen Zeile, sonst None.

        Vorrang hat die Nummer, auch die abweichende Nummer der Prüfziel-Tabelle
        (nr_tabelle). Der Name muss dann nur grob passen. Ohne passende Nummer
        entscheidet ein sehr ähnlicher Name.
        """
        im_teil = [e for e in self.pruefziele if teil in (None, e["teil"])]
        mit_nummer = [e for e in im_teil if nr in (e["nr"], e.get("nr_tabelle"))]
        wert, bester = aehnlichster(mit_nummer, name)
        if wert >= MIN_AEHNLICHKEIT_MIT_NUMMER:
            return bester
        if not name:
            return None
        wert, bester = aehnlichster(im_teil, name)
        return bester if wert >= MIN_AEHNLICHKEIT_OHNE_NUMMER else None


@functools.cache
def liste(schluessel: str = STANDARD) -> Liste:
    """Lädt eine Prüfziel-Liste, KeyError bei unbekanntem Schlüssel."""
    datei = DATEIEN.get(schluessel)
    if not datei:
        raise KeyError(f"Unbekannte Prüfziel-Liste: {schluessel}")
    daten = json.loads((DATEN / datei).read_text(encoding="utf-8"))
    return Liste(daten["schluessel"], daten["titel"], daten["quelle"], daten["eintraege"])


def auswahl() -> list[tuple[str, str]]:
    """Liefert (Schlüssel, Titel) aller Listen für Auswahlfelder."""
    return [(s, liste(s).titel) for s in DATEIEN]


def aus_text(text: str, name: str) -> Liste:
    """Liest eine Prüfziel-Liste aus dem Text einer Datei.

    Erkannt werden Zeilen mit Nummer und Name wie "VI.1.1.1 Karies" oder
    "1.1.1 Karies" und Überschriften wie "VI Erkrankungen". Nennt die Datei
    den Teil vor den Nummern, zählen nur solche Zeilen; das blendet Seitenzahlen
    und Fließtext aus. Ohne Teil zählen nur Nummern mit Punkt wie "1.1", eine
    einzelne Zahl ist dann meist eine Aufzählung im Fließtext. Die Tiefe der
    Nummer bestimmt die Ebene (EBENE_NACH_TIEFE). Prüfziele mit Unterpunkten
    zählen wie bei den eingebauten Listen nicht zur Vollständigkeit. Ohne
    erkannte Zeile ist die Liste leer.
    """
    zeilen = [zeile.strip() for zeile in text.splitlines()]
    mit_teil = any((treffer := _ZEILE.match(z)) and treffer.group(1) for z in zeilen)
    leser = _ListenLeser(nur_mit_teil=mit_teil)
    for zeile in zeilen:
        leser.zeile(zeile)
    return leser.liste(name)


def _oberpunkte(eintraege: list[Eintrag]) -> set[tuple[str, str]]:
    """Teil und Nummer aller Einträge, unter denen weitere Nummern stehen."""
    ober: set[tuple[str, str]] = set()
    for e in eintraege:
        zahlen = e["nr"].split(".")
        ober.update((e["teil"], ".".join(zahlen[:tiefe])) for tiefe in range(1, len(zahlen)))
    return ober


class _ListenLeser:
    """Sammelt die Einträge einer Prüfziel-Liste, Zeile für Zeile."""

    def __init__(self, *, nur_mit_teil: bool) -> None:
        self.eintraege: dict[tuple[str, str], Eintrag] = {}
        self._nur_mit_teil = nur_mit_teil
        self._teil = ""

    def zeile(self, zeile: str) -> None:
        """Verarbeitet eine Zeile ohne Leerraum am Rand."""
        ueberschrift = _TEIL_ZEILE.match(zeile)
        if ueberschrift:
            self._teil_beginnen(ueberschrift.group(1), ueberschrift.group(2))
            return
        treffer = _ZEILE.match(zeile)
        if not treffer or (self._nur_mit_teil and not treffer.group(1)):
            return
        teil, nr, name = treffer.groups()
        if not teil and "." not in nr:
            return
        if teil:
            self._teil_beginnen(teil, TEILE.get(teil, teil))
        name = re.sub(r"\s+", " ", _ANHANG.sub("", name)).strip()
        if len(name) >= MIN_NAME:
            ebene = EBENE_NACH_TIEFE.get(nr.count(".") + 1, "pruefziel")
            eintrag = {"ebene": ebene, "teil": self._teil, "nr": nr, "name": name}
            self.eintraege.setdefault((self._teil, nr), eintrag)

    def liste(self, name: str) -> Liste:
        """Liefert die gesammelten Einträge als Liste und markiert Prüfziele mit Unterpunkten."""
        eintraege = list(self.eintraege.values())
        ober = _oberpunkte(eintraege)
        for e in eintraege:
            if e["ebene"] == "pruefziel":
                e["unterpunkte"] = (e["teil"], e["nr"]) in ober
        return Liste(AUS_DATEI, name, name, eintraege)

    def _teil_beginnen(self, teil: str, name: str) -> None:
        self._teil = teil
        eintrag = {"ebene": "teil", "teil": teil, "nr": teil, "name": _ANHANG.sub("", name)}
        self.eintraege.setdefault((teil, teil), eintrag)
