"""Vorlesungsabgleich mit einer eigenen Prüfziel-Datei statt der eingebauten Liste."""

import io
import json

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.config import Grenzen
from tests.hilfen import (
    PRUEFZIEL_ANTWORTEN,
    FolienDienst,
    Seite,
    abfragen,
    abgleich_token,
    html_von,
    neuer_abgleich,
    uebernehmen,
    warten_bis_abgleich_fertig,
    zahl,
)

# Ein Kapitel im Format des IMPP-Katalogs
KAPITEL = (
    b"VI Erkrankungen\n"
    b"VI.1.2 Erkrankungen des Parodonts\n"
    b"VI.1.2.4 Parodontitis (2.3.1)\n"
    b"VI.1.2.5 Gingivitis und gingivale Erkrankungen\n"
)
DATEINAME = "Kapitel_VI_1.txt"


def _eigene_liste() -> tuple[io.BytesIO, str]:
    return io.BytesIO(KAPITEL), DATEINAME


def _ohne_datei() -> tuple[io.BytesIO, str]:
    """Ein leeres Dateifeld; der Test-Client schließt jede Datei nach der Anfrage."""
    return io.BytesIO(b""), ""


@pytest.fixture(name="token")
def fixture_token(angemeldet: FlaskClient, dienst: FolienDienst) -> str:
    """Ein fertiger Abgleich mit der eigenen Prüfziel-Datei."""
    dienst.antworten = PRUEFZIEL_ANTWORTEN
    antwort = neuer_abgleich(
        angemeldet, ziel="pruefziele", lernziele=_ohne_datei(), pruefziele=_eigene_liste()
    )
    token = abgleich_token(antwort)
    assert token is not None
    assert warten_bis_abgleich_fertig(angemeldet, token)["status"] == "fertig"
    return token


@pytest.mark.usefixtures("token")
def test_anfrage_nennt_die_datei(dienst: FolienDienst) -> None:
    """Das Modell erhält die Prüfziele der Datei statt der eingebauten Liste."""
    inhalt = dienst.bodies[-1]["messages"][1]["content"]
    assert inhalt.startswith(f"Prüfziele ({DATEINAME})")
    assert "1.2.5 Gingivitis und gingivale Erkrankungen" in inhalt


def test_datei_gespeichert(app: Flask, token: str) -> None:
    """Gespeichert werden Name und Text der Datei, keine eingebaute Liste."""
    gespeichert = abfragen(
        app, "select ziele_name, pruefziele_liste from folienabgleiche where token = ?", (token,)
    )[0]
    assert gespeichert["ziele_name"] == DATEINAME
    assert gespeichert["pruefziele_liste"] is None


def test_ergebnis_nach_der_datei(angemeldet: FlaskClient, token: str) -> None:
    """Angaben, die nicht in der Datei stehen, sind als unbekannt markiert."""
    folien = Seite(html_von(angemeldet.get(f"/folien/{token}")))
    assert folien.texte("chip") == ["VI 1.2.4", "VI 1.2.5", "VIII 99.9"]
    assert folien.texte("chip", "unbekannt") == ["VIII 99.9"]


@pytest.mark.parametrize(
    ("ansicht", "text"),
    [("ziele", "Nicht in der Prüfziel-Datei"), ("eingaben", DATEINAME)],
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
    antwort = neuer_abgleich(
        angemeldet,
        ziel="pruefziele",
        lernziele=_ohne_datei(),
        pruefziele=(io.BytesIO(notizen), "notizen.txt"),
    )
    assert "In der Datei stehen keine Prüfziele" in html_von(antwort)
    assert zahl(app, "select count(*) from folienabgleiche") == 0


@pytest.mark.usefixtures("dienst")
@pytest.mark.parametrize(
    ("felder", "meldung"),
    [
        ({}, "Lernziele: Die Datei hat"),
        (
            {"ziel": "pruefziele", "pruefziele": (io.BytesIO(KAPITEL), DATEINAME)},
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
        felder = {"lernziele": _ohne_datei(), **felder}
    html = html_von(neuer_abgleich(angemeldet, **felder))
    assert meldung in html
    assert "Bitte nur das passende Kapitel hochladen." in html
    assert zahl(app, "select count(*) from folienabgleiche") == 0


def test_uebernahme_mit_eigener_pruefziel_datei(angemeldet: FlaskClient) -> None:
    """Auch ein übernommenes Ergebnis lässt sich gegen eine eigene Prüfziel-Datei auswerten."""
    ergebnis = json.dumps(
        [
            {"folien-nr": 1, "Zuordnung": "VI 1.2.4"},
            {"folien-nr": 2, "Zuordnung": ["VI 1.2.5", "VI 9.9.9"]},
        ]
    ).encode()
    antwort = uebernehmen(
        angemeldet,
        ergebnis,
        "Ergebnis.json",
        ziel="pruefziele",
        lernziele=_ohne_datei(),
        pruefziele=_eigene_liste(),
    )
    token = abgleich_token(antwort)
    assert token is not None
    folien = Seite(html_von(angemeldet.get(f"/folien/{token}")))
    assert folien.texte("chip") == ["VI 1.2.4", "VI 1.2.5", "VI 9.9.9"]
    assert folien.texte("chip", "unbekannt") == ["VI 9.9.9"]
