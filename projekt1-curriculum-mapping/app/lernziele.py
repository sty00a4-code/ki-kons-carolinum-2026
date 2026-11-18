"""Lernziele eines NKLZ-Kapitels und Lernziel-IDs in Texten.

Eine Lernziel-ID besteht aus zwei bis fünf Zahlen mit Punkten, etwa 25.1.1.1.
"""

from __future__ import annotations

import re

MIN_WORTLAUT = 8
MAX_WORTLAUT = 600

_ID = re.compile(r"(?<![\d.])\d{1,2}(?:\.\d{1,2}){1,4}(?!\d)")
_ID_ZEILE = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){1,3})(?:\s+(.*))?$")
# Kompetenzstufe am Ende des Wortlauts
_STUFE_AM_ENDE = re.compile(r"\s(1|2|3a|3b)$")
# Zeilen, an denen der Wortlaut endet: Kompetenzstufe, Querverweise wie "5; 6", Seitenmarke
_ENDE = re.compile(r"^(?:(?:1|2|3a|3b)(?:\s|$)|\d+[a-z]?;|\[Seite)")


def ids(text: str | None) -> list[str]:
    """Liefert die Lernziel-IDs eines Textes ohne Dubletten, in der Reihenfolge des Textes."""
    return list(dict.fromkeys(_ID.findall(text or "")))


def aus_text(text: str | None) -> dict[str, str]:
    """Liest {Lernziel-ID: Wortlaut} aus dem Text eines NKLZ-Kapitels.

    Die ID steht am Zeilenanfang. Der Wortlaut endet an der Kompetenzstufe
    (1, 2, 3a, 3b), an Querverweisen wie "5; 6; 7" oder an der nächsten ID.
    Bei einem abweichenden Aufbau bleibt das Ergebnis leer.
    """
    leser = _KapitelLeser()
    for zeile in (text or "").splitlines():
        leser.zeile(zeile.strip())
    leser.abschliessen()
    return leser.ergebnis


class _KapitelLeser:
    """Sammelt den Wortlaut je Lernziel-ID, Zeile für Zeile."""

    def __init__(self) -> None:
        self.ergebnis: dict[str, str] = {}
        self._aktuell: str | None = None
        self._teile: list[str] = []

    def zeile(self, zeile: str) -> None:
        """Verarbeitet eine Zeile ohne Leerraum am Rand."""
        treffer = _ID_ZEILE.match(zeile)
        if treffer and ";" not in zeile:
            self._beginnen(treffer.group(1), (treffer.group(2) or "").strip())
        elif self._aktuell is not None:
            if _ENDE.match(zeile):
                self.abschliessen()
            elif zeile:
                self._teile.append(zeile)

    def abschliessen(self) -> None:
        """Legt den Wortlaut des aktuellen Lernziels ab."""
        if self._aktuell and self._teile:
            wortlaut = re.sub(r"\s+", " ", " ".join(self._teile)).strip()
            if len(wortlaut) > MIN_WORTLAUT:
                self.ergebnis.setdefault(self._aktuell, wortlaut[:MAX_WORTLAUT])
        self._aktuell = None

    def _beginnen(self, lernziel_id: str, rest: str) -> None:
        self.abschliessen()
        self._aktuell, self._teile = lernziel_id, []
        if not rest:
            return
        ende = _STUFE_AM_ENDE.search(rest)
        self._teile.append(rest[: ende.start()] if ende else rest)
        if ende:
            self.abschliessen()
