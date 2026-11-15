"""Antwort des Modells in Zeilen einer Zuordnung zerlegen.

Erwartet werden Zeilen im Format Prüfziel;Abdeckung;Begründung;Lernziel-ID.
lesen() toleriert übliche Abweichungen wie Markdown-Tabellen, Überschriften,
Aufzählungszeichen, Fettdruck oder eine vorangestellte Teilnummer ("VIII.").
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Final

from .. import lernziele
from ..ki import ohne_denkblock
from ..pruefziele import Eintrag

# Stufen der Abdeckung
ABGEDECKT: Final = 2
TEILWEISE: Final = 1
NICHT: Final = 0

# Längerer Text in der Spalte Abdeckung ist eine Begründung ohne Abdeckung.
MAX_ABDECKUNG = 12

_PRUEFZIEL = re.compile(r"^(?:(VIII|VI)\s*\.?\s*)?(\d{1,2}(?:\s*\.\s*\d{1,2}){0,4})\.?\s+(\S.*)$")
_TEIL = re.compile(r"^(VIII|VI)\b")
_AUFZAEHLUNG = re.compile(r"^(?:[-*•+]\s+|\d+\)\s+)")
_TRENNER = re.compile(r"^[\s|:=\-\u2013]+$")
_KEINE = frozenset({"-", "\u2013", "nein", "no", "o", "/"})
# Zusage am Anfang der Spalte Abdeckung, etwa "Ja, abgedeckt" oder "abgedeckt."
_JA = re.compile(r"^(?:ja|yes|abgedeckt|vollständig)\b")
# Wortteile und Zeichen in der Spalte Abdeckung
_VERNEINUNG = ("nicht", "kein")
_TEILWEISE = ("teil", "partiell")
_HAKEN = ("✓", "✔")


@dataclass
class Zeile:
    """Eine gelesene Zeile der Antwort.

    eintrag ist das Prüfziel der Liste, dem auswerten() die Zeile zuordnet.
    """

    teil: str | None
    nr: str
    name: str
    stufe: int
    begruendung: str
    lernziele: list[str] = field(default_factory=list)
    eintrag: Eintrag | None = None


def stufe(text: str | None) -> int:
    """Wandelt den Inhalt der Spalte Abdeckung in eine Stufe um."""
    t = re.sub(r"[*_()\[\]]", "", text or "").strip().lower()
    if not t or t in _KEINE or _enthaelt(t, _VERNEINUNG):
        return NICHT
    if _enthaelt(t, _TEILWEISE):
        return TEILWEISE
    if t.startswith("x") or _JA.match(t) or _enthaelt(t, _HAKEN):
        return ABGEDECKT
    return NICHT


def _enthaelt(text: str, teile: tuple[str, ...]) -> bool:
    return any(teil in text for teil in teile)


def beginnt_mit_pruefziel(text: str) -> bool:
    """Prüft, ob der Text mit Nummer und Name eines Prüfziels beginnt."""
    return bool(_PRUEFZIEL.match(_AUFZAEHLUNG.sub("", text)))


def lesen(text: str | None) -> tuple[list[Zeile], list[str]]:
    """Zerlegt den Antworttext in (erkannte Zeilen, nicht zuordenbare Zeilen)."""
    zeilen: list[Zeile] = []
    uebrig: list[str] = []
    teil = None
    for roh in ohne_denkblock(text).splitlines():
        s = _AUFZAEHLUNG.sub("", _ohne_markup(roh.strip()))
        if not s or _TRENNER.match(s):
            continue
        zellen = _zellen(s)
        if zellen is None:
            # Zeilen ohne Spalten zählen nur als Überschrift eines Teils.
            ueberschrift = _TEIL.match(s)
            teil = ueberschrift.group(1) if ueberschrift else teil
            continue
        if zellen[0].lower().startswith(("prüfziel", "pruefziel")):
            continue
        treffer = _PRUEFZIEL.match(_AUFZAEHLUNG.sub("", zellen[0]))
        if treffer:
            zeilen.append(_zeile(treffer, zellen[1:], teil))
        else:
            uebrig.append(roh.strip())
    return zeilen, uebrig


def _zellen(zeile: str) -> list[str] | None:
    """Teilt eine Zeile an Semikolons oder als Markdown-Tabelle; None ohne Spalten."""
    if ";" in zeile:
        return [z.strip() for z in zeile.split(";")]
    if "|" in zeile:
        return [z.strip() for z in zeile.strip("|").split("|")]
    return None


def _zeile(treffer: re.Match[str], rest: list[str], teil: str | None) -> Zeile:
    abdeckung = rest[0] if rest else ""
    begruendung, ids = _begruendung_und_ids(rest[1:])
    if (
        len(abdeckung) > MAX_ABDECKUNG
        and stufe(abdeckung) == NICHT
        and not abdeckung.lower().startswith("x")
    ):
        begruendung = _verbinden("; ", abdeckung, begruendung)
        abdeckung = ""
    genannt = lernziele.ids(ids)
    if not genannt and ids.strip():
        begruendung = _verbinden(" ", begruendung, _ohne_hervorhebung(ids))
    return Zeile(
        teil=treffer.group(1) or teil,
        nr=re.sub(r"\s+", "", treffer.group(2)),
        name=treffer.group(3).strip().rstrip(":").strip(),
        stufe=stufe(abdeckung),
        begruendung=_ohne_hervorhebung(begruendung),
        lernziele=genannt,
    )


def _begruendung_und_ids(spalten: list[str]) -> tuple[str, str]:
    """Liefert (Begründung, Lernziel-IDs) aus den Spalten nach der Abdeckung."""
    if len(spalten) >= 2:
        return "; ".join(s for s in spalten[:-1] if s.strip()), spalten[-1]
    if spalten:
        # Bei nur einer Spalte fehlen entweder die IDs oder die Begründung.
        return ("", spalten[0]) if lernziele.ist_id(spalten[0]) else (spalten[0], "")
    return "", ""


def _verbinden(trenner: str, *teile: str) -> str:
    return trenner.join(t for t in teile if t.strip())


def _ohne_markup(text: str) -> str:
    text = text.replace("**", "").replace("__", "")
    return re.sub(r"^#+\s*", "", text).strip()


def _ohne_hervorhebung(text: str) -> str:
    """Entfernt Hervorhebung und äußere Klammern, etwa bei "*(Keine Abdeckung)*"."""
    t = text.strip().strip("*_ ").strip()
    if t.startswith("(") and t.endswith(")"):
        t = t[1:-1].strip()
    return t
