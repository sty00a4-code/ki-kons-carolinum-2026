"""Mehrere Ergebnisse derselben Prüfziel-Liste je Prüfziel gegenüberstellen."""

from __future__ import annotations

import itertools
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from ..pruefziele import Eintrag, Liste
from .antwort import Zeile
from .auswertung import Ergebnis, pruefziele_mit_koepfen

# Das Ergebnis, zu dem eine Auswertung gehört, etwa eine Zeile der Datenbank
T = TypeVar("T")


@dataclass(frozen=True)
class Vergleichszeile:
    """Kopfzeile (art "teil", "bereich", "gruppe") oder Prüfziel mit einer Zelle je Ergebnis."""

    art: str
    eintrag: Eintrag
    zellen: list[Zeile | None] = field(default_factory=list)
    einig: bool = False


@dataclass(frozen=True)
class Paar(Generic[T]):
    """Übereinstimmung zweier Ergebnisse bei den Prüfzielen, die beide beantworten."""

    a: T
    b: T
    gemeinsam: int
    gleich: int
    kappa: float | None

    @property
    def anteil(self) -> int:
        """Anteil der Prüfziele mit gleicher Abdeckung in Prozent."""
        return round(self.gleich / self.gemeinsam * 100) if self.gemeinsam else 0


@dataclass(frozen=True)
class Vergleich(Generic[T]):
    """Vergleichstabelle und Übereinstimmung für jedes Paar von Ergebnissen.

    gleich zählt die zählenden Prüfziele mit derselben Abdeckung in allen
    Ergebnissen, zaehlend alle zählenden Prüfziele der Liste.
    """

    zeilen: list[Vergleichszeile]
    gleich: int
    zaehlend: int
    paare: list[Paar[T]]


def kappa(a: Sequence[int], b: Sequence[int]) -> float | None:
    """Berechnet Kappa nach Cohen für zwei gleich lange Listen von Stufen."""
    n = len(a)
    if not n:
        return None
    beobachtet = sum(x == y for x, y in zip(a, b, strict=True)) / n
    ca, cb = Counter(a), Counter(b)
    erwartet = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    if erwartet >= 1:
        return 1.0 if beobachtet == 1 else None
    return (beobachtet - erwartet) / (1 - erwartet)


def vergleichen(laeufe: Sequence[tuple[T, Ergebnis]], liste: Liste) -> Vergleich[T]:
    """Stellt mehrere Ergebnisse je Prüfziel gegenüber.

    laeufe enthält Paare aus einem beliebigen Bezug, etwa der Zeile der
    Datenbank, und dem ausgewerteten Ergebnis. Je Prüfziel zählt die erste
    Zeile eines Ergebnisses.
    """
    je_lauf = [_erste_zeilen(ergebnis) for _, ergebnis in laeufe]
    zeilen, gleich = _zeilen(je_lauf, liste)
    paare = [
        _paar(laeufe[i][0], laeufe[j][0], je_lauf[i], je_lauf[j], liste)
        for i, j in itertools.combinations(range(len(laeufe)), 2)
    ]
    return Vergleich(zeilen, gleich, len(liste.zaehlend), paare)


def _erste_zeilen(ergebnis: Ergebnis) -> dict[str, Zeile]:
    erste: dict[str, Zeile] = {}
    for z in ergebnis.zeilen:
        if z.eintrag:
            erste.setdefault(z.eintrag["schluessel"], z)
    return erste


def _zeilen(je_lauf: list[dict[str, Zeile]], liste: Liste) -> tuple[list[Vergleichszeile], int]:
    zeilen: list[Vergleichszeile] = []
    gleich = 0
    for koepfe, e in pruefziele_mit_koepfen(liste):
        zellen = [lauf.get(e["schluessel"]) for lauf in je_lauf]
        if e.get("unterpunkte") and not any(zellen):
            continue
        einig = _einig(zellen)
        if einig and not e.get("unterpunkte"):
            gleich += 1
        zeilen.extend(Vergleichszeile(kopf["ebene"], kopf) for kopf in koepfe.abgeben())
        zeilen.append(Vergleichszeile("zeile", e, zellen, einig))
    return zeilen, gleich


def _einig(zellen: list[Zeile | None]) -> bool:
    """Alle Ergebnisse haben eine Zeile zum Prüfziel, mit derselben Stufe."""
    stufen = {z.stufe if z else None for z in zellen}
    return len(stufen) == 1 and None not in stufen


def _paar(
    a: T, b: T, zeilen_a: dict[str, Zeile], zeilen_b: dict[str, Zeile], liste: Liste
) -> Paar[T]:
    gemeinsam = [
        e["schluessel"]
        for e in liste.zaehlend
        if e["schluessel"] in zeilen_a and e["schluessel"] in zeilen_b
    ]
    stufen_a = [zeilen_a[s].stufe for s in gemeinsam]
    stufen_b = [zeilen_b[s].stufe for s in gemeinsam]
    gleich = sum(x == y for x, y in zip(stufen_a, stufen_b, strict=True))
    return Paar(a, b, len(gemeinsam), gleich, kappa(stufen_a, stufen_b))
