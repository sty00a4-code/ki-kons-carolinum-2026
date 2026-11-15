"""Vorlesungsabgleich: ungültige Eingaben, unlesbare Ergebnisdateien und Fortsetzen."""

import io
import json
from typing import Any

import openpyxl
import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.config import Grenzen, KiEinstellungen
from tests.hilfen import (
    ausfuehren,
    csrf,
    html_von,
    neuer_abgleich,
    uebernehmen,
    zahl,
)

ZAHL_ABGLEICHE = "select count(*) from folienabgleiche"


def _excel(*zeilen: list[Any], blatt: str = "Folien") -> bytes:
    mappe = openpyxl.Workbook()
    tabelle = mappe.active
    assert tabelle is not None
    tabelle.title = blatt
    for zeile in zeilen:
        tabelle.append(zeile)
    puffer = io.BytesIO()
    mappe.save(puffer)
    return puffer.getvalue()


@pytest.mark.usefixtures("dienst")
@pytest.mark.parametrize(
    ("aenderung", "meldung"),
    [
        ({"ziel": "quatsch"}, "mit Lernzielen oder mit Prüfzielen"),
        ({"ziel": "pruefziele", "liste": "gibt-es-nicht"}, "Prüfziel-Liste aus der Auswahl"),
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


@pytest.mark.parametrize(
    ("datei", "name", "meldung"),
    [
        (b'{"folien-nr": 1}', "objekt.json", "muss eine Liste"),
        (json.dumps([1, {"Zuordnung": "25.1.1.1"}]).encode(), "ohne_nr.json", "keine Folien"),
        (json.dumps([{"folien-nr": "Titel"}]).encode(), "ohne_zahl.json", "keine Folien"),
        (_excel(["Spalte A", "Spalte B"], [1, "25.1.1.1"]), "ohne_kopf.xlsx", "keine Folien"),
        (_excel(blatt="Leer"), "leer.xlsx", "keine Folien"),
        (b"weder noch", "kaputt.xlsx", "weder eine Excel-Datei"),
    ],
)
def test_unlesbare_ergebnisdateien(
    app: Flask, angemeldet: FlaskClient, datei: bytes, name: str, meldung: str
) -> None:
    """Ergebnisdateien ohne erkennbare Folien werden mit Hinweis abgelehnt."""
    assert meldung in html_von(uebernehmen(angemeldet, datei, name))
    assert zahl(app, ZAHL_ABGLEICHE) == 0


def test_uebernahme_aus_excel_mit_bildbeschreibung(angemeldet: FlaskClient) -> None:
    """Eine Excel-Datei mit Bildspalte liefert auch die Bildbeschreibung."""
    datei = _excel(
        ["Folie", "Lernziele", "Bildbeschreibung"],
        [1, "25.1.1.1", "Ein Diagramm."],
        [2, "25.3.1.1"],
    )
    antwort = uebernehmen(angemeldet, datei, "Ergebnis.xlsx")
    assert antwort.status_code == 302
    html = html_von(angemeldet.get(antwort.headers["Location"]))
    assert "Ein Diagramm." in html


def test_uebernahme_ohne_modell(app: Flask, angemeldet: FlaskClient) -> None:
    """Ohne Angabe des Modells wird nichts übernommen."""
    datei = json.dumps([{"folien-nr": 1, "Zuordnung": "25.1.1.1"}]).encode()
    assert "welches Modell" in html_von(uebernehmen(angemeldet, datei, "e.json", modell=""))
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
