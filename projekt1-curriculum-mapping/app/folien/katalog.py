"""Ziele eines Vorlesungsabgleichs: Lernziele oder Prüfziele.

Ein Katalog enthält die Ziele in der Reihenfolge ihres Dokuments, dazwischen
Überschriften für Teil, Bereich und Gruppe. text ist die Liste für das
Modell, lesen() ordnet die Angaben einer Antwort den Einträgen zu.
"""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass, field

from .. import lernziele, pruefziele
from ..ki import ohne_denkblock


@dataclass(frozen=True)
class Zielart:
    """Womit eine Vorlesung abgeglichen wird, mit den Wortformen für die Seiten."""

    name: str
    einzahl: str
    dativ: str


ZIELARTEN = {
    "lernziele": Zielart("Lernziele", "Lernziel", "Lernzielen"),
    "pruefziele": Zielart("Prüfziele", "Prüfziel", "Prüfzielen"),
}

# Eine Prüfziel-Nummer wie "VI 1.2.3" oder "1.2" in einer Antwort
_PRUEFZIEL_ANGABE = re.compile(
    r"(?<![\w.])(?:(VIII|VI)\s*\.?\s*)?(\d{1,2}(?:\.\d{1,2}){1,3})(?!\.?\d)"
)


@dataclass(frozen=True)
class Ziel:
    """Eintrag eines Katalogs: ein Ziel (art "ziel") oder eine Überschrift.

    art ist bei Überschriften "teil", "bereich" oder "gruppe". Für die
    Abdeckung zählen nur Einträge mit zaehlt. teil, nr und nr_tabelle haben
    nur Prüfziele.
    """

    art: str
    schluessel: str
    name: str
    zaehlt: bool
    teil: str | None = None
    nr: str | None = None
    nr_tabelle: str | None = None

    @property
    def anzeige(self) -> str:
        """Kurzbezeichnung wie "25.1.1.1" oder "VI 1.1.1"."""
        if self.nr is None:
            return self.schluessel
        if self.art == "teil":
            return self.nr
        return f"{self.teil or ''} {self.nr}".strip()


@dataclass
class Katalog:
    """Ziele eines Abgleichs in der Reihenfolge ihres Dokuments.

    quelle benennt das Dokument für die Seiten, etwa "Prüfziel-Datei".
    """

    art: str
    titel: str
    quelle: str
    eintraege: list[Ziel]
    text: str
    zaehlend: list[Ziel] = field(init=False)
    _nach_schluessel: dict[str, Ziel] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.zaehlend = [e for e in self.eintraege if e.zaehlt]
        self._nach_schluessel = {e.schluessel: e for e in self.eintraege}

    def lesen(self, antwort: str) -> tuple[list[Ziel], list[str]]:
        """Liefert (Einträge, unbekannte Angaben) einer Antwort, jeweils ohne Dubletten."""
        text = ohne_denkblock(antwort)
        if self.art == "lernziele":
            angaben = [(lid, self._nach_schluessel.get(lid)) for lid in lernziele.ids(text)]
        else:
            angaben = [paar for zeile in text.splitlines() for paar in self._pruefziele(zeile)]
        treffer: dict[str, Ziel] = {}
        unbekannt: dict[str, None] = {}
        for angabe, eintrag in angaben:
            if eintrag:
                treffer.setdefault(eintrag.schluessel, eintrag)
            else:
                unbekannt.setdefault(angabe, None)
        return list(treffer.values()), list(unbekannt)

    def _pruefziele(self, zeile: str) -> Iterator[tuple[str, Ziel | None]]:
        """Liefert (Angabe, Eintrag oder None) für jede Prüfziel-Nummer einer Zeile.

        Ohne Teil ist eine Nummer mehrdeutig, wenn es sie in VI und VIII gibt.
        Dann entscheidet der Name, falls die Zeile nur eine Nummer enthält.
        """
        funde = list(_PRUEFZIEL_ANGABE.finditer(zeile))
        for treffer in funde:
            teil, nr = treffer.groups()
            kandidaten = self._mit_nummer(teil, nr)
            if len(kandidaten) > 1 and len(funde) == 1:
                kandidaten = _nach_name(kandidaten, zeile[treffer.end() :].strip(" -:;,"))
            angabe = f"{teil} {nr}" if teil else nr
            yield angabe, kandidaten[0] if len(kandidaten) == 1 else None

    def _mit_nummer(self, teil: str | None, nr: str) -> list[Ziel]:
        """Prüfziele und Gruppen mit der Nummer, im genannten Teil oder ohne Teil."""
        return [
            e
            for e in self.eintraege
            if e.art in ("ziel", "gruppe")
            and nr in (e.nr, e.nr_tabelle)
            and (teil is None or not e.teil or teil == e.teil)
        ]


def _nach_name(kandidaten: list[Ziel], name: str) -> list[Ziel]:
    """Wählt unter mehreren Kandidaten den mit dem ähnlichsten Namen, falls er ähnlich genug ist."""
    if not name:
        return kandidaten
    wert, bester = max(
        ((pruefziele.aehnlichkeit(e.name, name), e) for e in kandidaten),
        key=lambda paar: paar[0],
    )
    return [bester] if wert >= pruefziele.MIN_AEHNLICHKEIT_MIT_NUMMER else []


def lernziel_katalog(text: str | None, name: str | None = None) -> Katalog:
    """Liest die Lernziele eines NKLZ-Kapitels.

    IDs, unter denen weitere IDs stehen (etwa 25.1), sind Überschriften.
    """
    texte = lernziele.aus_text(text)
    koepfe = {lid for lid in texte if any(i.startswith(f"{lid}.") for i in texte)}
    oberste = min((lid.count(".") for lid in koepfe), default=0)
    eintraege: list[Ziel] = []
    zeilen: list[str] = []
    for lid, wortlaut in texte.items():
        art = "ziel"
        if lid in koepfe:
            art = "bereich" if lid.count(".") == oberste else "gruppe"
            if zeilen:
                zeilen.append("")
        eintraege.append(Ziel(art, lid, wortlaut, zaehlt=art == "ziel"))
        zeilen.append(f"{lid} {wortlaut}")
    titel = f"Lernziele ({name})" if name else "Lernziele"
    return Katalog("lernziele", titel, "Lernziel-Datei", eintraege, "\n".join(zeilen))


def pruefziel_katalog(liste: pruefziele.Liste) -> Katalog:
    """Übernimmt eine Prüfziel-Liste. Prüfziele mit Unterpunkten zählen nicht zur Abdeckung."""
    eintraege = [
        Ziel(
            art="ziel" if e["ebene"] == "pruefziel" else e["ebene"],
            schluessel=e["schluessel"],
            name=e["name"],
            zaehlt=e["ebene"] == "pruefziel" and not e.get("unterpunkte"),
            teil=e["teil"],
            nr=e["nr"],
            nr_tabelle=e.get("nr_tabelle"),
        )
        for e in liste.eintraege
    ]
    quelle = "Prüfziel-Datei" if liste.schluessel == pruefziele.AUS_DATEI else "Prüfziel-Liste"
    return Katalog(
        "pruefziele", f"Prüfziele ({liste.titel})", quelle, eintraege, liste.text_fuer_modell()
    )


def katalog(abgleich: sqlite3.Row) -> Katalog:
    """Katalog eines gespeicherten Abgleichs.

    Prüfziele stammen aus der hochgeladenen Datei, falls es eine gibt, sonst
    aus der gewählten eingebauten Liste.
    """
    if abgleich["ziel"] == "lernziele":
        return lernziel_katalog(abgleich["ziele_text"], abgleich["ziele_name"])
    if abgleich["ziele_text"]:
        return pruefziel_katalog(
            pruefziele.aus_text(abgleich["ziele_text"], abgleich["ziele_name"])
        )
    return pruefziel_katalog(pruefziele.liste(abgleich["pruefziele_liste"]))
