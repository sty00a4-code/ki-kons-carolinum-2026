"""Optionale Prüfung mit einer echten Ergebnis-Excel, gesteuert über Umgebungsvariablen.

    P1_TEST_EXCEL="ModellAuswertung Mistral.xlsx" \\
    P1_TEST_LERNZIELE=NKLZLernziele242248.pdf pytest tests/test_echte_dateien.py
"""

import os

import pytest

from app import dokumente
from app.pruefziele import Liste
from app.zuordnung.auswertung import Ergebnis, auswerten
from app.zuordnung.excel_import import blaetter

TEST_EXCEL = os.environ.get("P1_TEST_EXCEL", "")
TEST_LERNZIELE = os.environ.get("P1_TEST_LERNZIELE", "")

pytestmark = pytest.mark.skipif(
    not os.path.exists(TEST_EXCEL), reason="P1_TEST_EXCEL nicht gesetzt oder Datei fehlt"
)


@pytest.fixture(name="lernziele_text")
def fixture_lernziele_text() -> str:
    """Text der Lernziel-PDF, leer wenn P1_TEST_LERNZIELE fehlt."""
    if not os.path.exists(TEST_LERNZIELE):
        return ""
    with open(TEST_LERNZIELE, "rb") as datei:
        return str(dokumente.aufraeumen(dokumente.pdf_text(datei.read())))


@pytest.fixture(name="ergebnisse")
def fixture_ergebnisse(liste: Liste, lernziele_text: str) -> dict[str, Ergebnis]:
    """Ausgewertete Blätter der Excel, je Blattname."""
    with open(TEST_EXCEL, "rb") as datei:
        gelesen = blaetter(datei.read())
    return {b.name: auswerten(b.text, liste, lernziele_text) for b in gelesen}


def test_zeilen_je_blatt(ergebnisse: dict[str, Ergebnis]) -> None:
    """Kontrollzahlen der drei Blätter (Temperatur 0.0, 0.5 und 1.0)."""
    assert [len(e.zeilen) for e in ergebnisse.values()] == [143, 143, 141]


def test_alle_zeilen_einem_pruefziel_zugeordnet(ergebnisse: dict[str, Ergebnis]) -> None:
    """Keine Zeile bleibt unlesbar oder ohne Prüfziel."""
    assert all(not e.uebrig and not e.ohne_liste for e in ergebnisse.values())


def test_abdeckung_wie_in_der_excel(ergebnisse: dict[str, Ergebnis]) -> None:
    """Die Zahl der X je Blatt entspricht der Excel."""
    assert [e.abgedeckt for e in ergebnisse.values()] == [116, 124, 86]


def test_unbekannte_ids_im_blatt_1_0(ergebnisse: dict[str, Ergebnis], lernziele_text: str) -> None:
    """Mit Lernziel-Datei werden die unbekannten IDs des Blatts 1.0 erkannt."""
    if not lernziele_text:
        pytest.skip("P1_TEST_LERNZIELE nicht gesetzt oder Datei fehlt")
    unbekannt = [sorted(e.unbekannte_ids) for e in ergebnisse.values()]
    assert unbekannt[2] == ["4.5.2", "4.5.2.4", "4.5.2.5", "4.5.2.6"]
