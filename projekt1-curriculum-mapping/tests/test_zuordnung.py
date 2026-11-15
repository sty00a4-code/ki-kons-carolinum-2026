"""Zuordnung nach Kategorie 1: Durchlauf gegen den Testserver, Ansichten, Wiederholen, Löschen."""

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.pruefziele import Liste
from tests.hilfen import (
    ZWEITES_MODELL,
    KiZustand,
    Lauf,
    Seite,
    csrf,
    html_von,
    neue_zuordnung,
    token_aus,
    warten_bis_fertig,
    zahl,
)

ZAHL_AUSWERTUNGEN = "select count(*) from auswertungen"


def test_ohne_schluessel_startet_nichts(angemeldet: FlaskClient) -> None:
    """Ohne API-Schlüssel weist das Formular darauf hin und startet keinen Lauf."""
    assert "noch kein Schlüssel" in html_von(angemeldet.get("/neu"))
    antwort = neue_zuordnung(angemeldet)
    assert antwort.status_code == 200
    assert "kein Schlüssel" in html_von(antwort)


def test_upload_leitet_zum_ergebnis(durchlauf: Lauf) -> None:
    """Der Upload legt ein Ergebnis an und der Durchlauf endet fertig."""
    assert durchlauf.token is not None
    assert durchlauf.stand["status"] == "fertig", durchlauf.stand


def test_anfrage_an_den_dienst(durchlauf: Lauf, ki_zustand: KiZustand) -> None:
    """Endpunkt, Schlüssel, Stream und Temperatur der Anfrage stimmen."""
    assert durchlauf.token is not None
    anfrage = ki_zustand.anfragen[-1]
    assert anfrage.pfad == "/v1/chat/completions"
    assert anfrage.auth == "Bearer test-schluessel"
    assert anfrage.body["stream"] is True
    assert anfrage.body["temperature"] == 0.5


def test_inhalt_der_anfrage(durchlauf: Lauf) -> None:
    """Dokumente stehen in der Reihenfolge der Verweise im Prompt, der Prompt am Ende."""
    inhalt = durchlauf.anfragen[-1]["messages"][1]["content"]
    assert (
        inhalt.index("Dokument 1: Prüfziele")
        < inhalt.index("Dokument 2: Lernziele")
        < inhalt.index("Dokument 3: Vorlesung")
    )
    assert "25.1.1.1 wichtige relevante Erkrankungen" in inhalt
    assert "Parodontitis als Manifestation" in inhalt
    assert inhalt.rstrip().endswith("ordne die Lernziele zu.")


def test_ergebnistabelle(angemeldet: FlaskClient, ergebnis_token: str, liste: Liste) -> None:
    """Kacheln und Tabelle zeigen die Zuordnung, der Denk-Abschnitt fehlt."""
    html = html_von(angemeldet.get(f"/ergebnisse/{ergebnis_token}"))
    abgedeckt = sum(1 for i, _ in enumerate(liste.zaehlend) if i % 3) + 1
    assert f'<div class="mv">{abgedeckt}</div>' in html
    assert html.count('data-stufe="2"') == abgedeckt
    assert "Nicht in der Prüfziel-Liste" in html
    assert "25.9.9.9" in html
    assert "chip unbekannt" in html
    assert "wichtige relevante Erkrankungen erkennen" in html
    assert "Ich gehe die Liste" not in html


@pytest.mark.parametrize("ansicht", ["lernziele", "antwort", "eingaben"])
def test_ansichten_laden(angemeldet: FlaskClient, ergebnis_token: str, ansicht: str) -> None:
    """Jede Ansicht des Ergebnisses lädt."""
    antwort = angemeldet.get(f"/ergebnisse/{ergebnis_token}?ansicht={ansicht}")
    assert antwort.status_code == 200


def test_dateiname_unter_eingaben(angemeldet: FlaskClient, ergebnis_token: str) -> None:
    """Unter Eingaben steht der Name der hochgeladenen Vorlesung."""
    html = html_von(angemeldet.get(f"/ergebnisse/{ergebnis_token}?ansicht=eingaben"))
    assert "Vorlesung_1.pdf" in html


def test_formular_nennt_zahl_der_pruefziele(angemeldet: FlaskClient, liste: Liste) -> None:
    """Das Formular nennt die Zahl der Prüfziele der Liste."""
    assert f"{len(liste.zaehlend)} Prüfziele" in html_von(angemeldet.get("/neu"))


def test_wiederholen_legt_neues_ergebnis_an(
    angemeldet: FlaskClient, ergebnis_token: str, ki_zustand: KiZustand
) -> None:
    """Erneut ausführen nutzt neues Modell und neue Temperatur mit der gespeicherten Vorlesung."""
    modell = ZWEITES_MODELL
    antwort = angemeldet.post(
        f"/ergebnisse/{ergebnis_token}/wiederholen",
        data={
            "_csrf_token": csrf(angemeldet, "/neu"),
            "modell": modell,
            "temperatur": "1",
            "prompt": "Neuer Prompt für den zweiten Lauf.",
        },
    )
    neu = token_aus(antwort)
    assert neu is not None
    assert neu != ergebnis_token
    assert warten_bis_fertig(angemeldet, neu)["status"] == "fertig"
    body = ki_zustand.anfragen[-1].body
    assert body["model"] == modell
    assert body["temperature"] == 1.0
    assert "Parodontitis als Manifestation" in body["messages"][1]["content"]


def test_wiederholen_mit_fehler_behaelt_eingaben(
    app: Flask, angemeldet: FlaskClient, ergebnis_token: str
) -> None:
    """Ein Fehler beim erneuten Ausführen behält die Eingaben und legt nichts an."""
    vorher = zahl(app, ZAHL_AUSWERTUNGEN)
    modell = ZWEITES_MODELL
    antwort = angemeldet.post(
        f"/ergebnisse/{ergebnis_token}/wiederholen",
        data={
            "_csrf_token": csrf(angemeldet, "/neu"),
            "modell": modell,
            "temperatur": "5",
            "prompt": "Geänderter Prompt, der nicht verloren gehen darf.",
        },
    )
    html = html_von(antwort)
    assert antwort.status_code == 200
    assert "zwischen 0 und 2" in html
    assert "Geänderter Prompt, der nicht verloren gehen darf." in html
    assert 'value="5"' in html
    assert Seite(html).ausgewaehlt["modell"] == modell
    assert zahl(app, ZAHL_AUSWERTUNGEN) == vorher


@pytest.mark.parametrize("pfad", ["/neu", "/import", "/ergebnisse/{token}?ansicht=eingaben"])
def test_entwurf_im_browser(angemeldet: FlaskClient, ergebnis_token: str, pfad: str) -> None:
    """Die Seiten mit Formularen binden den Entwurf im Browser ein."""
    html = html_von(angemeldet.get(pfad.format(token=ergebnis_token)))
    for teil in ("seiten.js", "data-entwurf=", "entwurf-hinweis", "entwurf-verwerfen"):
        assert teil in html, pfad


def test_entwurfsskript_wird_ausgeliefert(angemeldet: FlaskClient) -> None:
    """entwurf.js liegt unter /static und nutzt localStorage."""
    skript = angemeldet.get("/static/entwurf.js")
    assert skript.status_code == 200
    assert b"localStorage" in skript.data
    skript.close()


def test_loeschen_entfernt_das_ergebnis(angemeldet: FlaskClient, ergebnis_token: str) -> None:
    """Löschen leitet weiter, danach ergibt das Ergebnis 404."""
    antwort = angemeldet.post(
        f"/ergebnisse/{ergebnis_token}/loeschen", data={"_csrf_token": csrf(angemeldet, "/neu")}
    )
    assert antwort.status_code == 302
    assert angemeldet.get(f"/ergebnisse/{ergebnis_token}").status_code == 404
