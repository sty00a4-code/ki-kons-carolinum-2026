"""Vorlesungsabgleich: Durchlauf, Ansichten, Vorschaubilder und Eingabefehler."""

import io

import pytest
from flask import Flask
from flask.testing import FlaskClient

from tests.hilfen import (
    BILD,
    BILDMODELL,
    FOLIEN_PDF,
    VORLESUNG_PDF,
    FolienDienst,
    Lauf,
    Seite,
    abgleich_token,
    balkenwerte,
    csrf,
    html_von,
    neuer_abgleich,
    warten_bis_abgleich_fertig,
    zahl,
)


def test_abgleich_wird_fertig(abgleich: Lauf) -> None:
    """Ein neuer Abgleich leitet zum Ergebnis und bearbeitet alle vier Folien."""
    assert abgleich.token is not None
    assert abgleich.stand == {"status": "fertig", "fertig": 4, "gesamt": 4, "fehler": None}


def test_je_folie_zwei_anfragen(abgleich: Lauf, dienst: FolienDienst) -> None:
    """Je Folie gibt es eine Bild- und eine Zuordnungsanfrage."""
    assert abgleich.token is not None
    assert dienst.bilder == 4
    assert dienst.folien == [1, 2, 3, 4]


def test_bildanfrage(abgleich: Lauf) -> None:
    """Die Bildanfrage nutzt das Bildmodell und ein JPEG."""
    bild = abgleich.anfragen[0]
    url = bild["messages"][1]["content"][1]["image_url"]["url"]
    assert bild["model"] == BILDMODELL
    assert url.startswith("data:image/jpeg;base64,/9j/")


def test_zuordnungsanfrage(abgleich: Lauf) -> None:
    """Die Zuordnung läuft ohne Stream und enthält alle Angaben der Folie."""
    anfrage = abgleich.anfragen[1]
    inhalt = anfrage["messages"][1]["content"]
    assert anfrage["stream"] is False
    assert anfrage["temperature"] == 0
    assert inhalt.startswith("Lernziele (Lernziele_Kapitel_25.pdf)")
    assert "25.1.1.1 wichtige relevante Erkrankungen" in inhalt
    assert "Textinhalt: Diabetes mellitus und Parodontitis" in inhalt
    assert f"Bild: {BILD}" in inhalt
    assert inhalt.endswith("gelehrt werden.")


def test_kacheln_und_markierungen(angemeldet: FlaskClient, folien_token: str) -> None:
    """Kacheln zählen Folien und Lernziele, unbekannte IDs sind markiert."""
    html = html_von(angemeldet.get(f"/folien/{folien_token}"))
    assert '<div class="mv">3</div>' in html
    assert "4 <small>von 4</small>" in html
    assert Seite(html).texte("chip", "unbekannt") == ["25.9.9.9"]
    assert "Die Folie behandelt" not in html


@pytest.mark.parametrize("ansicht", ["ziele", "antworten", "eingaben"])
def test_ansichten_laden(angemeldet: FlaskClient, folien_token: str, ansicht: str) -> None:
    """Jede Ansicht des Abgleichs lädt."""
    assert angemeldet.get(f"/folien/{folien_token}?ansicht={ansicht}").status_code == 200


def test_balken_je_lernziel(angemeldet: FlaskClient, folien_token: str) -> None:
    """Jedes der fünf Lernziele steht auf genau einer Folie."""
    assert balkenwerte(angemeldet, folien_token) == ["1", "1", "1", "1", "1"]


def test_vorschaubild(angemeldet: FlaskClient, folien_token: str) -> None:
    """Das Vorschaubild ist ein JPEG und nur privat zwischengespeichert."""
    antwort = angemeldet.get(f"/folien/{folien_token}/folie/2.jpg")
    assert antwort.status_code == 200
    assert antwort.data[:2] == b"\xff\xd8"
    assert "private" in antwort.headers["Cache-Control"]


def test_vorschau_fehlender_folie(angemeldet: FlaskClient, folien_token: str) -> None:
    """Die Vorschau einer fehlenden Folie ergibt 404."""
    assert angemeldet.get(f"/folien/{folien_token}/folie/9.jpg").status_code == 404


def test_pdf_der_vorlesung_abrufbar(angemeldet: FlaskClient, folien_token: str) -> None:
    """Die hochgeladene PDF-Datei lässt sich wieder abrufen."""
    antwort = angemeldet.get(f"/folien/{folien_token}/vorlesung.pdf")
    assert antwort.status_code == 200
    assert antwort.data == FOLIEN_PDF


@pytest.mark.usefixtures("dienst")
def test_lernziel_datei_ohne_ids_abgelehnt(angemeldet: FlaskClient) -> None:
    """Eine Lernziel-Datei ohne IDs wird abgelehnt."""
    antwort = neuer_abgleich(angemeldet, lernziele=(io.BytesIO(VORLESUNG_PDF), "Vorlesung.pdf"))
    assert "keine Lernziel-IDs" in html_von(antwort)


@pytest.mark.usefixtures("dienst")
def test_vorlesung_muss_pdf_sein(angemeldet: FlaskClient) -> None:
    """Die Vorlesung muss eine PDF-Datei sein."""
    antwort = neuer_abgleich(angemeldet, vorlesung=(io.BytesIO(b"kein pdf"), "Vorlesung.txt"))
    assert "als PDF hochladen" in html_von(antwort)


def test_loeschen_entfernt_folien_und_pdf(
    app: Flask, angemeldet: FlaskClient, folien_token: str
) -> None:
    """Beim Löschen verschwinden die Folien und die PDF-Datei des Abgleichs."""
    zweiter = abgleich_token(neuer_abgleich(angemeldet))
    assert zweiter is not None
    warten_bis_abgleich_fertig(angemeldet, zweiter)
    anzahl = zahl(app, "select count(*) from folien")
    angemeldet.post(
        f"/folien/{folien_token}/loeschen",
        data={"_csrf_token": csrf(angemeldet, f"/folien/{folien_token}")},
    )
    assert angemeldet.get(f"/folien/{folien_token}").status_code == 404
    rest = zahl(app, "select count(*) from folien")
    pdfs = zahl(app, "select count(*) from vorlesungen")
    abgleiche = zahl(app, "select count(*) from folienabgleiche")
    assert rest == anzahl - 4
    assert pdfs == abgleiche
