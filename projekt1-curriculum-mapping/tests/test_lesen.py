"""Lesen der Modellantwort und Auswahl der Prüfziele, ohne Anwendung und Netzwerk."""

import pytest

from app import lernziele, pruefziele
from app.folien.katalog import Katalog, Ziel, pruefziel_katalog
from app.pruefziele import Liste
from app.zuordnung import antwort
from app.zuordnung.antwort import ABGEDECKT, NICHT, TEILWEISE
from app.zuordnung.auswertung import Ergebnis, auswerten
from app.zuordnung.vergleich import kappa
from tests.hilfen import modellantwort

LERNZIELE_TEXT = (
    "25.1.1.1 wichtige Erkrankungen erkennen. 2\n"
    "25.2.1.5 Wechselwirkungen. 2\n"
    "25.3.1.1 Infektionen. 3a"
)

VARIANTEN = """
| Prüfziel | Abdeckung | Begründung | Lernziel-ID |
|---|---|---|---|
| 1.1.1 Karies | X | Wird unter Allgemeinerkrankungen behandelt. | 25.1.1.1 |
- **1.1.2 Erosion, Abrasion, Attrition**; teilweise; nur am Rand; 25.2.1.5
VIII Übergeordnete Kompetenzen
VIII.4.5.7 Behinderung und Gesundheit;;*(Keine direkte Abdeckung)*
"""


@pytest.fixture(name="ergebnis")
def fixture_ergebnis(liste: Liste) -> Ergebnis:
    """Ausgewertete Antwort im Format des Prompts mit typischen Abweichungen."""
    return auswerten(modellantwort(liste), liste, LERNZIELE_TEXT)


@pytest.fixture(name="varianten")
def fixture_varianten(liste: Liste) -> Ergebnis:
    """Ausgewertete Antwort in abweichenden Schreibweisen."""
    return auswerten(VARIANTEN, liste)


def test_alle_zeilen_gelesen(ergebnis: Ergebnis, liste: Liste) -> None:
    """Jede Zeile der Antwort wird gelesen, auch die zusätzliche."""
    assert len(ergebnis.zeilen) == len(liste.zaehlend) + 1


def test_kein_pruefziel_fehlt(ergebnis: Ergebnis) -> None:
    """Zu jedem Prüfziel der Liste gibt es eine Zeile."""
    assert not ergebnis.fehlend


def test_erfundenes_pruefziel_steht_ausserhalb(ergebnis: Ergebnis) -> None:
    """Eine Zeile ohne Prüfziel der Liste wird getrennt geführt."""
    assert len(ergebnis.ohne_liste) == 1


def test_unbekannte_id_erkannt(ergebnis: Ergebnis) -> None:
    """Lernziel-IDs, die in der Lernziel-Datei fehlen, werden gemeldet."""
    assert ergebnis.unbekannte_ids == {"25.9.9.9"}


def test_keine_unlesbaren_zeilen(ergebnis: Ergebnis) -> None:
    """Alle Zeilen der Antwort sind lesbar."""
    assert not ergebnis.uebrig


def test_nicht_abgedeckte_gezaehlt(ergebnis: Ergebnis, liste: Liste) -> None:
    """Jedes dritte Prüfziel ist in der Antwort nicht abgedeckt."""
    erwartet = sum(1 for i, _ in enumerate(liste.zaehlend) if i % 3 == 0)
    assert ergebnis.nicht == erwartet


@pytest.mark.parametrize(
    ("text", "erwartet"),
    [
        ("X", ABGEDECKT),
        ("Ja, abgedeckt", ABGEDECKT),
        ("abgedeckt.", ABGEDECKT),
        ("Vollständig abgedeckt", ABGEDECKT),
        ("✓", ABGEDECKT),
        ("teilweise abgedeckt", TEILWEISE),
        ("nicht abgedeckt", NICHT),
        ("Nein", NICHT),
        ("Die Folie behandelt das Thema ja nur am Rande", NICHT),
        ("", NICHT),
        (None, NICHT),
    ],
)
def test_stufe_der_spalte_abdeckung(text: str | None, erwartet: int) -> None:
    """Zusagen zählen am Anfang der Spalte, Verneinungen und "teilweise" gehen vor."""
    assert antwort.stufe(text) == erwartet


@pytest.mark.parametrize(
    ("schluessel", "stufe", "beschreibung"),
    [
        ("VI-1.1.1", ABGEDECKT, "Tabelle mit senkrechten Strichen"),
        ("VI-1.1.2", TEILWEISE, "Aufzählung mit Fettdruck und teilweise"),
        ("VIII-4.5.7", NICHT, "VIII. vor der Nummer und Hinweis in Klammern"),
    ],
)
def test_schreibweisen(varianten: Ergebnis, schluessel: str, stufe: int, beschreibung: str) -> None:
    """Abweichende Schreibweisen der Zeilen werden gelesen."""
    stufen = {z.eintrag["schluessel"]: z.stufe for z in varianten.zeilen if z.eintrag}
    assert stufen.get(schluessel) == stufe, beschreibung


def test_hinweis_ohne_sternchen_und_klammern(varianten: Ergebnis) -> None:
    """Ein Hinweis in Sternchen und Klammern wird als Klartext gespeichert."""
    hinweis = next((z.begruendung for z in varianten.zeilen if z.nr == "4.5.7"), "")
    assert hinweis == "Keine direkte Abdeckung"


def test_nummer_aus_der_pruefziel_tabelle(liste: Liste) -> None:
    """Eine abweichende Nummer wird über den Namen dem Prüfziel zugeordnet."""
    abweichend = auswerten("4.12.2 Depression;X;passt;25.1.1.2", liste)
    assert abweichend.zeilen
    eintrag = abweichend.zeilen[0].eintrag
    assert eintrag is not None
    assert eintrag["nr"] == "4.13.2"


def test_kappa_bei_voller_uebereinstimmung() -> None:
    """Kappa ist 1, wenn beide Läufe übereinstimmen."""
    assert kappa([2, 0, 2, 0], [2, 0, 2, 0]) == 1.0


def test_kappa_bei_zufallsniveau() -> None:
    """Kappa ist 0, wenn die Übereinstimmung dem Zufall entspricht."""
    wert = kappa([2, 2, 0, 0], [2, 0, 2, 0])
    assert wert is not None
    assert abs(wert) < 1e-9


@pytest.fixture(name="doppelt")
def fixture_doppelt() -> tuple[Katalog, Ziel]:
    """Ein Katalog mit einer Nummer, die in zwei Teilen der Liste vorkommt."""
    katalog = pruefziel_katalog(pruefziele.liste(pruefziele.STANDARD))
    eintrag = next(
        e
        for e in katalog.eintraege
        if e.art == "ziel" and sum(x.nr == e.nr and x.art == "ziel" for x in katalog.eintraege) > 1
    )
    return katalog, eintrag


def test_mehrdeutige_nummer_bleibt_offen(doppelt: tuple[Katalog, Ziel]) -> None:
    """Eine Nummer in VI und VIII ohne Teil wird nicht geraten."""
    katalog, eintrag = doppelt
    assert eintrag.nr is not None
    treffer, unbekannt = katalog.lesen(eintrag.nr)
    assert not treffer
    assert unbekannt == [eintrag.nr]


def test_name_entscheidet_bei_mehrdeutiger_nummer(doppelt: tuple[Katalog, Ziel]) -> None:
    """Mit dem Namen ist auch eine mehrdeutige Nummer eindeutig."""
    katalog, eintrag = doppelt
    treffer, _ = katalog.lesen(f"{eintrag.nr} {eintrag.name}")
    assert treffer == [eintrag]


def test_lernziele_aus_kapiteltext() -> None:
    """Der Wortlaut endet an Stufe, Querverweis oder Seitenmarke, über Zeilen hinweg."""
    text = (
        "25.1.1.1 Erkrankungen der Mundschleimhaut\n"
        "erkennen und benennen\n"
        "2\n"
        "25.1.1.2\n"
        "Wechselwirkungen von Arzneimitteln beschreiben\n"
        "5; 6\n"
        "25.1.1.3 Kurz\n"
        "[Seite 2]\n"
        "25.1.1.4 Befunde einordnen und bewerten 3a\n"
        "Fließtext ohne Lernziel"
    )
    assert lernziele.aus_text(text) == {
        "25.1.1.1": "Erkrankungen der Mundschleimhaut erkennen und benennen",
        "25.1.1.2": "Wechselwirkungen von Arzneimitteln beschreiben",
        "25.1.1.4": "Befunde einordnen und bewerten",
    }


@pytest.mark.parametrize(
    ("text", "erwartet"),
    [("25.1.1.1, 25.2", True), ("25.1.1.1 und mehr", False), ("ohne", False)],
)
def test_ist_id(text: str, erwartet: bool) -> None:  # noqa: FBT001
    """Nur Text aus IDs und Trennzeichen gilt als ID-Angabe."""
    assert lernziele.ist_id(text) is erwartet
