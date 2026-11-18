"""Vorlesungsabgleich: ungültige Eingaben, Fortsetzen und Wiederholen."""

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.config import Grenzen, KiEinstellungen
from tests.hilfen import (
    ausfuehren,
    csrf,
    html_von,
    neuer_abgleich,
    zahl,
)

ZAHL_ABGLEICHE = "select count(*) from folienabgleiche"


@pytest.mark.usefixtures("dienst")
@pytest.mark.parametrize(
    ("aenderung", "meldung"),
    [
        ({"ziel": "quatsch"}, "mit Lernzielen oder mit Prüfzielen"),
        ({"ziel": "pruefziele"}, "Prüfziele: Bitte eine Datei auswählen"),
        ({"bildmodell": "gibt-es-nicht"}, "Bildmodell aus der Liste"),
    ],
)
def test_eingabefehler_beim_abgleich(
    app: Flask, angemeldet: FlaskClient, aenderung: dict[str, str], meldung: str
) -> None:
    """Ungültige Eingaben ergeben eine Meldung und keinen Abgleich."""
    assert meldung in html_von(neuer_abgleich(angemeldet, **aenderung))
    assert zahl(app, ZAHL_ABGLEICHE) == 0


@pytest.mark.usefixtures("dienst")
def test_zu_viele_folien(app: Flask, angemeldet: FlaskClient) -> None:
    """Eine Vorlesung mit mehr Seiten als erlaubt wird abgelehnt."""
    app.config["GRENZEN"] = Grenzen(folien=2)
    assert "erlaubt sind 2" in html_von(neuer_abgleich(angemeldet))
    assert zahl(app, ZAHL_ABGLEICHE) == 0


def test_ohne_schluessel_kein_abgleich(app: Flask, angemeldet: FlaskClient) -> None:
    """Ohne Schlüssel für den KI-Dienst startet kein Abgleich."""
    assert "P1_LLM_API_KEY" in html_von(neuer_abgleich(angemeldet))
    assert zahl(app, ZAHL_ABGLEICHE) == 0


def test_unbekannte_ansicht_und_unbekannte_vorlesung(
    angemeldet: FlaskClient, folien_token: str
) -> None:
    """Eine unbekannte Ansicht zeigt die Folien, unbekannte Abgleiche ergeben 404."""
    html = html_von(angemeldet.get(f"/folien/{folien_token}?ansicht=gibt-es-nicht"))
    assert 'id="folie-1"' in html
    assert angemeldet.get("/folien/gibt-es-nicht/vorlesung").status_code == 404


def _fortsetzen(angemeldet: FlaskClient, token: str) -> str:
    antwort = angemeldet.post(
        f"/folien/{token}/fortsetzen", data={"_csrf_token": csrf(angemeldet, f"/folien/{token}")}
    )
    return html_von(angemeldet.get(antwort.headers["Location"]))


def test_fertiger_abgleich_laesst_sich_nicht_fortsetzen(
    angemeldet: FlaskClient, folien_token: str
) -> None:
    """Nur abgebrochene Abgleiche lassen sich fortsetzen."""
    assert "Nur abgebrochene Abgleiche" in _fortsetzen(angemeldet, folien_token)


def test_fortsetzen_ohne_schluessel(app: Flask, angemeldet: FlaskClient, folien_token: str) -> None:
    """Ohne Schlüssel lässt sich ein abgebrochener Abgleich nicht fortsetzen."""
    ausfuehren(app, "update folienabgleiche set status = 'fehler', fehler = 'Abbruch'")
    app.config["KI"] = KiEinstellungen()
    assert "kein Schlüssel hinterlegt" in _fortsetzen(angemeldet, folien_token)


def test_wiederholen_mit_fehler_behaelt_eingaben(
    app: Flask, angemeldet: FlaskClient, folien_token: str
) -> None:
    """Ein Fehler beim erneuten Ausführen zeigt die Eingaben wieder an."""
    antwort = angemeldet.post(
        f"/folien/{folien_token}/wiederholen",
        data={
            "_csrf_token": csrf(angemeldet, f"/folien/{folien_token}?ansicht=eingaben"),
            "modell": "gibt-es-nicht",
            "temperatur": "1,5",
            "prompt": "Ein geänderter Prompt für den Abgleich.",
        },
    )
    html = html_von(antwort)
    assert "Modell aus der Liste" in html
    assert "Ein geänderter Prompt für den Abgleich." in html
    assert 'value="1,5"' in html
    assert zahl(app, ZAHL_ABGLEICHE) == 1
