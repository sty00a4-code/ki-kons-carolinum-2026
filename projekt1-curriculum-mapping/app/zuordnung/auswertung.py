"""Zeilen einer Antwort der Prüfziel-Liste zuordnen und die Abdeckung zählen."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass

from .. import lernziele
from ..pruefziele import Eintrag, Liste
from .antwort import ABGEDECKT, NICHT, TEILWEISE, Zeile, lesen

# Ebenen der Kopfzeilen, von oben nach unten
EBENEN = ("teil", "bereich", "gruppe")
# Lernziele der untersten Ebene haben mindestens so viele Punkte in der ID.
PUNKTE_UNTERSTE_EBENE = 3

OHNE_LISTE: Eintrag = {"nr": "", "name": "Nicht in der Prüfziel-Liste"}


class Kopfzeilen:
    """Merkt sich Teil, Bereich und Gruppe bis zur nächsten belegten Tabellenzeile.

    So erscheinen Kopfzeilen nur über Zeilen, die tatsächlich angezeigt werden.
    """

    def __init__(self) -> None:
        self._offen: list[Eintrag] = []

    def merken(self, eintrag: Eintrag) -> None:
        """Nimmt einen Teil, Bereich oder eine Gruppe auf und schließt tiefere Ebenen."""
        tiefe = EBENEN.index(eintrag["ebene"])
        self._offen = [k for k in self._offen if EBENEN.index(k["ebene"]) < tiefe]
        self._offen.append(eintrag)

    def abgeben(self) -> list[Eintrag]:
        """Liefert die offenen Kopfzeilen und vergisst sie."""
        offen, self._offen = self._offen, []
        return offen


def pruefziele_mit_koepfen(liste: Liste) -> Iterator[tuple[Kopfzeilen, Eintrag]]:
    """Liefert jedes Prüfziel der Liste mit den Kopfzeilen, die darüber offen sind."""
    koepfe = Kopfzeilen()
    for e in liste.eintraege:
        if e["ebene"] == "pruefziel":
            yield koepfe, e
        else:
            koepfe.merken(e)


@dataclass(frozen=True)
class Tabellenzeile:
    """Zeile der Ergebnistabelle.

    art ist "teil", "bereich" oder "gruppe" bei Kopfzeilen, "zeile" bei einer
    Zeile der Antwort und "fehlt" bei einem Prüfziel ohne Zeile.
    """

    art: str
    eintrag: Eintrag | None
    zeile: Zeile | None = None


@dataclass(frozen=True)
class LernzielTreffer:
    """Ein Lernziel mit den Zeilen der Antwort, die es einem Prüfziel zuordnen."""

    id: str
    text: str
    zeilen: list[Zeile]
    unbekannt: bool = False

    @property
    def anzahl(self) -> int:
        """Anzahl der Prüfziele, denen das Lernziel zugeordnet ist."""
        return len(self.zeilen)


@dataclass(frozen=True)
class Ergebnis:
    """Ausgewertete Antwort eines Durchlaufs.

    Die Zähler beziehen sich auf die Zeilen der Antwort. fehlend enthält die
    zählenden Prüfziele der Liste, zu denen keine Zeile vorliegt, zaehlend
    die Anzahl aller zählenden Prüfziele.
    """

    zeilen: list[Zeile]
    uebrig: list[str]
    tabelle: list[Tabellenzeile]
    zaehlend: int
    fehlend: list[Eintrag]
    lernziele: list[LernzielTreffer]
    lernziel_texte: dict[str, str]

    @property
    def abgedeckt(self) -> int:
        """Zeilen mit der Abdeckung X."""
        return self._mit_stufe(ABGEDECKT)

    @property
    def teilweise(self) -> int:
        """Zeilen mit teilweiser Abdeckung."""
        return self._mit_stufe(TEILWEISE)

    @property
    def nicht(self) -> int:
        """Zeilen ohne Abdeckung."""
        return self._mit_stufe(NICHT)

    @property
    def anteil(self) -> int:
        """Anteil der abgedeckten Zeilen in Prozent."""
        return round(self.abgedeckt / len(self.zeilen) * 100) if self.zeilen else 0

    @property
    def ohne_liste(self) -> list[Zeile]:
        """Zeilen, die zu keinem Prüfziel der Liste passen."""
        return [z for z in self.zeilen if z.eintrag is None]

    @property
    def unbekannte_ids(self) -> set[str]:
        """Genannte Lernziel-IDs, die im Lernziel-Dokument nicht vorkommen."""
        return {lz.id for lz in self.lernziele if lz.unbekannt}

    @property
    def ids_genannt(self) -> int:
        """Anzahl der Lernziele, die mindestens einem Prüfziel zugeordnet sind."""
        return sum(1 for lz in self.lernziele if lz.anzahl)

    @property
    def ungenutzt(self) -> list[LernzielTreffer]:
        """Lernziele aus dem Dokument, die keinem Prüfziel zugeordnet sind."""
        return [lz for lz in self.lernziele if not lz.anzahl]

    def _mit_stufe(self, stufe: int) -> int:
        return sum(1 for z in self.zeilen if z.stufe == stufe)


def auswerten(text: str | None, liste: Liste, lernziele_text: str | None = None) -> Ergebnis:
    """Ordnet die Zeilen einer Antwort der Prüfziel-Liste zu und zählt die Abdeckung."""
    zeilen, uebrig = lesen(text)
    je_eintrag: defaultdict[str, list[Zeile]] = defaultdict(list)
    ohne_liste: list[Zeile] = []
    for z in zeilen:
        z.eintrag = liste.finde(z.teil, z.nr, z.name)
        if z.eintrag:
            je_eintrag[z.eintrag["schluessel"]].append(z)
        else:
            ohne_liste.append(z)
    texte = lernziele.aus_text(lernziele_text)
    return Ergebnis(
        zeilen=zeilen,
        uebrig=uebrig,
        tabelle=_tabelle(liste, je_eintrag, ohne_liste),
        zaehlend=len(liste.zaehlend),
        fehlend=[e for e in liste.zaehlend if e["schluessel"] not in je_eintrag],
        lernziele=_lernziele(zeilen, texte, lernziele_text or ""),
        lernziel_texte=texte,
    )


def _lernziele(
    zeilen: list[Zeile], texte: dict[str, str], lernziele_text: str
) -> list[LernzielTreffer]:
    """Liefert die genannten Lernziele mit ihren Zeilen.

    Es zählen nur Zeilen mit Abdeckung. Danach folgen die Lernziele der
    untersten Ebene aus dem Dokument, die keine Zeile nennt.
    """
    bekannt = set(texte) or set(lernziele.ids(lernziele_text))
    je_id = _je_lernziel(zeilen)
    unbekannt = {lid for lid in je_id if bekannt and lid not in bekannt}
    treffer = [
        LernzielTreffer(lid, texte.get(lid, ""), je_id[lid], lid in unbekannt)
        for lid in sorted(je_id, key=lernziele.sortierschluessel)
    ]
    treffer.extend(
        LernzielTreffer(lid, texte[lid], [])
        for lid in sorted(set(texte) - set(je_id), key=lernziele.sortierschluessel)
        if lid.count(".") >= PUNKTE_UNTERSTE_EBENE
    )
    return treffer


def _je_lernziel(zeilen: list[Zeile]) -> dict[str, list[Zeile]]:
    """Zeilen mit Abdeckung je genannter Lernziel-ID."""
    je_id: defaultdict[str, list[Zeile]] = defaultdict(list)
    for z in zeilen:
        if z.stufe != NICHT:
            for lernziel_id in z.lernziele:
                je_id[lernziel_id].append(z)
    return je_id


def _tabelle(
    liste: Liste, je_eintrag: dict[str, list[Zeile]], ohne_liste: list[Zeile]
) -> list[Tabellenzeile]:
    """Liefert die Zeilen der Ergebnistabelle in der Reihenfolge der Prüfziel-Liste."""
    ausgabe: list[Tabellenzeile] = []
    for koepfe, e in pruefziele_mit_koepfen(liste):
        treffer = je_eintrag.get(e["schluessel"], [])
        if not treffer and e.get("unterpunkte"):
            continue
        ausgabe.extend(Tabellenzeile(kopf["ebene"], kopf) for kopf in koepfe.abgeben())
        if treffer:
            ausgabe.extend(Tabellenzeile("zeile", e, z) for z in treffer)
        else:
            ausgabe.append(Tabellenzeile("fehlt", e))
    if ohne_liste:
        ausgabe.append(Tabellenzeile("teil", OHNE_LISTE))
        ausgabe.extend(Tabellenzeile("zeile", None, z) for z in ohne_liste)
    return ausgabe
