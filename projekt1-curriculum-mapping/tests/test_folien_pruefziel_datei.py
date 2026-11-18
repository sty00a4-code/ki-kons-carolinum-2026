"""Vorlesungsabgleich mit Prüfzielen aus einer hochgeladenen Datei."""

import io

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.config import Grenzen
from tests.hilfen import (
    PRUEFZIEL_ANTWORTEN,
    PRUEFZIEL_DATEINAME,
    PRUEFZIEL_KAPITEL,
    FolienDienst,
    Seite,
    abfragen,
    abgleich_token,
    html_von,
    neuer_abgleich,
    neuer_pruefziel_abgleich,
    ohne_datei,
    warten_bis_abgleich_fertig,
    zahl,
)


@pytest.fixture(name="token")
def fixture_token(angemeldet: FlaskClient, dienst: FolienDienst) -> str:
    """Ein fertiger Abgleich mit der Prüfziel-Datei."""
    dienst.antworten = PRUEFZIEL_ANTWORTEN
    token = abgleich_token(neuer_pruefziel_abgleich(angemeldet))
    assert token is not None
    assert warten_bis_abgleich_fertig(angemeldet, token)["status"] == "fertig"
    return token


@pytest.mark.usefixtures("token")
def test_anfrage_nennt_die_datei(dienst: FolienDienst) -> None:
    """Das Modell erhält die Prüfziele der Datei."""
    inhalt = dienst.bodies[-1]["messages"][1]["content"]
    assert inhalt.startswith(f"Prüfziele ({PRUEFZIEL_DATEINAME})")
    assert "1.2.5 Gingivitis und gingivale Erkrankungen" in inhalt


def test_datei_gespeichert(app: Flask, token: str) -> None:
    """Gespeichert werden Name und Text der Datei."""
    gespeichert = abfragen(
        app, "select ziele_name, ziele_text from folienabgleiche where token = ?", (token,)
    )[0]
    assert gespeichert["ziele_name"] == PRUEFZIEL_DATEINAME
    assert gespeichert["ziele_text"] == PRUEFZIEL_KAPITEL.decode().strip()


def test_ergebnis_nach_der_datei(angemeldet: FlaskClient, token: str) -> None:
    """Angaben, die nicht in der Datei stehen, sind als unbekannt markiert."""
    folien = Seite(html_von(angemeldet.get(f"/folien/{token}")))
    assert folien.texte("chip") == ["VI 1.2.4", "VI 1.2.5", "VIII 99.9"]
    assert folien.texte("chip", "unbekannt") == ["VIII 99.9"]


@pytest.mark.parametrize(
    ("ansicht", "text"),
    [("ziele", "Nicht in der Prüfziel-Datei"), ("eingaben", PRUEFZIEL_DATEINAME)],
)
def test_ansichten_nennen_die_datei(
    angemeldet: FlaskClient, token: str, ansicht: str, text: str
) -> None:
    """Die Ansichten Ziele und Eingaben beziehen sich auf die Datei."""
    assert text in html_von(angemeldet.get(f"/folien/{token}?ansicht={ansicht}"))


@pytest.mark.usefixtures("dienst")
def test_datei_ohne_pruefziele_wird_abgelehnt(app: Flask, angemeldet: FlaskClient) -> None:
    """Eine Datei ohne erkennbare Prüfziele ergibt eine Meldung und keinen Abgleich."""
    notizen = b"Nur Fliesstext ohne Nummern. Er ist lang genug, damit die App ihn liest."
    antwort = neuer_pruefziel_abgleich(angemeldet, pruefziele=(io.BytesIO(notizen), "notizen.txt"))
    assert "In der Datei stehen keine Prüfziele" in html_von(antwort)
    assert zahl(app, "select count(*) from folienabgleiche") == 0


@pytest.mark.usefixtures("dienst")
@pytest.mark.parametrize(
    ("felder", "meldung"),
    [
        ({}, "Lernziele: Die Datei hat"),
        (
            {
                "ziel": "pruefziele",
                "pruefziele": (io.BytesIO(PRUEFZIEL_KAPITEL), PRUEFZIEL_DATEINAME),
            },
            "Prüfziele: Die Datei hat",
        ),
    ],
)
def test_zu_lange_ziel_datei_wird_abgelehnt(
    app: Flask, angemeldet: FlaskClient, felder: dict[str, object], meldung: str
) -> None:
    """Auch die Datei mit den Zielen darf nicht länger als erlaubt sein."""
    app.config["GRENZEN"] = Grenzen(zeichen=50)
    if felder:
        felder = {"lernziele": ohne_datei(), **felder}
    html = html_von(neuer_abgleich(angemeldet, **felder))
    assert meldung in html
    assert "Bitte nur das passende Kapitel hochladen." in html
    assert zahl(app, "select count(*) from folienabgleiche") == 0
