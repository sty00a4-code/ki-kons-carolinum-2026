"""Lesen der Ziele und der Modellantwort, ohne Anwendung und Netzwerk."""

import pytest

from app import lernziele, pruefziele
from app.folien.katalog import Katalog, Ziel, lernziel_katalog, pruefziel_katalog

# Dieselbe Nummer steht in zwei Teilen der Liste.
MEHRDEUTIG = """\
VI Erkrankungen
VI.1.1.1 Karies
VI.4.5.7 Depression
VIII Übergeordnete Kompetenzen
VIII.1.1.1 Kommunikation mit Patientinnen und Patienten
VIII.4.5.7 Behinderung und Gesundheit
"""
LERNZIELE_TEXT = (
    "25.1 Allgemeinerkrankungen\n"
    "25.1.1.1 wichtige Erkrankungen erkennen. 2\n"
    "25.2.1.5 Wechselwirkungen. 2\n"
    "25.3.1.1 Infektionen. 3a"
)


@pytest.fixture(name="doppelt")
def fixture_doppelt() -> tuple[Katalog, Ziel]:
    """Ein Katalog mit einer Nummer, die in zwei Teilen der Liste vorkommt."""
    katalog = pruefziel_katalog(pruefziele.aus_text(MEHRDEUTIG, "Katalog.txt"))
    eintrag = next(e for e in katalog.zaehlend if e.teil == "VI" and e.nr == "4.5.7")
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


def test_teil_entscheidet_bei_mehrdeutiger_nummer(doppelt: tuple[Katalog, Ziel]) -> None:
    """Mit dem Teil ist eine mehrdeutige Nummer eindeutig."""
    katalog, eintrag = doppelt
    treffer, unbekannt = katalog.lesen("VI 4.5.7")
    assert treffer == [eintrag]
    assert not unbekannt


def test_lernziel_katalog_liest_ids_und_meldet_unbekannte() -> None:
    """Bekannte IDs werden zugeordnet, andere als unbekannt gemeldet, Denkblöcke gelten nicht."""
    katalog = lernziel_katalog(LERNZIELE_TEXT, "Kapitel.txt")
    antwort = "<think>25.3.1.1</think>25.1.1.1, 25.2.1.5 und 25.9.9.9"
    treffer, unbekannt = katalog.lesen(antwort)
    assert [e.schluessel for e in treffer] == ["25.1.1.1", "25.2.1.5"]
    assert unbekannt == ["25.9.9.9"]
    assert [e.schluessel for e in katalog.zaehlend] == ["25.1.1.1", "25.2.1.5", "25.3.1.1"]


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
