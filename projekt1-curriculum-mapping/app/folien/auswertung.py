"""Antworten eines Vorlesungsabgleichs je Folie und je Ziel zusammenfassen."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass

from . import speicher
from .katalog import Katalog, Ziel, katalog

MAX_FOLIENTITEL = 160


@dataclass(frozen=True)
class Folie:
    """Eine Folie mit den Zielen aus der Antwort.

    ziele sind die Einträge des Katalogs, unbekannt die übrigen Angaben.
    titel ist die erste Zeile des Folientextes.
    """

    nr: int
    text: str
    bild: str | None
    antwort: str | None
    ziele: list[Ziel]
    unbekannt: list[str]

    @property
    def offen(self) -> bool:
        """Die Folie ist noch nicht bearbeitet."""
        return self.antwort is None

    @property
    def titel(self) -> str:
        """Erste nicht leere Zeile des Folientextes."""
        zeile = next((z.strip() for z in self.text.splitlines() if z.strip()), "")
        return zeile[:MAX_FOLIENTITEL]


@dataclass(frozen=True)
class Zielzeile:
    """Ein Eintrag des Katalogs mit den Nummern der Folien, die ihn nennen."""

    eintrag: Ziel
    folien: list[int]


@dataclass(frozen=True)
class Ergebnis:
    """Ausgewertete Antworten eines Abgleichs.

    unbekannt enthält je Angabe ohne Eintrag im Katalog die Nummern der
    Folien, die sie nennen.
    """

    folien: list[Folie]
    zeilen: list[Zielzeile]
    unbekannt: dict[str, list[int]]

    @property
    def gesamt(self) -> int:
        """Anzahl der Folien."""
        return len(self.folien)

    @property
    def bearbeitet(self) -> int:
        """Anzahl der Folien mit Antwort."""
        return sum(1 for f in self.folien if not f.offen)

    @property
    def mit_zuordnung(self) -> int:
        """Anzahl der Folien, denen mindestens ein Ziel zugeordnet ist."""
        return sum(1 for f in self.folien if f.ziele)

    @property
    def zaehlend(self) -> int:
        """Anzahl der Ziele, die für die Abdeckung zählen."""
        return sum(1 for z in self.zeilen if z.eintrag.zaehlt)

    @property
    def abgedeckt(self) -> int:
        """Anzahl der zählenden Ziele mit mindestens einer Folie."""
        return sum(1 for z in self.zeilen if z.eintrag.zaehlt and z.folien)

    @property
    def max_folien(self) -> int:
        """Höchste Zahl von Folien je Eintrag, mindestens 1; Maßstab der Balken."""
        anzahlen = [len(z.folien) for z in self.zeilen] + [len(n) for n in self.unbekannt.values()]
        return max([1, *anzahlen])


def auswerten(zeilen: Iterable[sqlite3.Row], ziele: Katalog) -> Ergebnis:
    """Liest die Antwort jeder Folie und zählt die Folien je Ziel."""
    je_eintrag: dict[str, list[int]] = {e.schluessel: [] for e in ziele.eintraege}
    unbekannt: dict[str, list[int]] = {}
    folien = []
    for z in zeilen:
        treffer, fremd = ziele.lesen(z["antwort"]) if z["antwort"] else ([], [])
        for e in treffer:
            je_eintrag[e.schluessel].append(z["nr"])
        for angabe in fremd:
            unbekannt.setdefault(angabe, []).append(z["nr"])
        folien.append(
            Folie(z["nr"], z["folientext"], z["bildbeschreibung"], z["antwort"], treffer, fremd)
        )
    tabelle = [Zielzeile(e, je_eintrag[e.schluessel]) for e in ziele.eintraege]
    return Ergebnis(folien, tabelle, unbekannt)


def ergebnis(
    con: sqlite3.Connection, abgleich: sqlite3.Row, ziele: Katalog | None = None
) -> Ergebnis:
    """Wertet die gespeicherten Antworten eines Abgleichs aus."""
    return auswerten(speicher.folien(con, abgleich["id"]), ziele or katalog(abgleich))
