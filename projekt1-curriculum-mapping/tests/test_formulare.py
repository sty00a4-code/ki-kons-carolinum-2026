"""Prüfung der Eingaben im Formular eines neuen Abgleichs."""

import io

import pytest
from flask import Flask
from flask.testing import FlaskClient

from tests.hilfen import neuer_abgleich, neuer_pruefziel_abgleich, zahl

ZAHL_ABGLEICHE = "select count(*) from folienabgleiche"
TEXT = "25.1.1.1 Erkrankungen erkennen und in der Therapieplanung berücksichtigen. 2\n"


@pytest.mark.usefixtures("dienst")
def test_textdatei_in_latin_1(app: Flask, angemeldet: FlaskClient) -> None:
    """Textdateien dürfen auch in Latin-1 kodiert sein."""
    lernziele = (io.BytesIO(TEXT.encode("latin-1") * 2), "lernziele.txt")
    assert neuer_abgleich(angemeldet, lernziele=lernziele).status_code == 302
    assert zahl(app, ZAHL_ABGLEICHE) == 1


@pytest.mark.usefixtures("dienst")
def test_pruefziel_datei_in_latin_1(app: Flask, angemeldet: FlaskClient) -> None:
    """Auch die Prüfziel-Datei darf in Latin-1 kodiert sein."""
    kapitel = "VI Erkrankungen\nVI.1.2.4 Parodontitis, Zähne und Mundschleimhaut\n"
    datei = (io.BytesIO(kapitel.encode("latin-1")), "Kapitel.txt")
    assert neuer_pruefziel_abgleich(angemeldet, pruefziele=datei).status_code == 302
    assert zahl(app, ZAHL_ABGLEICHE) == 1
