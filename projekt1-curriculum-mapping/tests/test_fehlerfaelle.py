"""Fehler des KI-Dienstes, ungültige Eingaben, gleichzeitige Läufe und Grenzwerte."""

import io
from typing import Any

import openpyxl
import pytest
from flask import Flask
from flask.testing import FlaskClient
from pypdf import PdfWriter
from werkzeug.datastructures import FileStorage
from werkzeug.test import encode_multipart

from tests.hilfen import (
    MB,
    FolienDienst,
    KiZustand,
    abgleich_token,
    ausfuehren,
    csrf,
    html_von,
    neuer_abgleich,
    warten_bis_abgleich_fertig,
    zahl,
)

ZAHL_ABGLEICHE = "select count(*) from folienabgleiche"


def _geschuetzte_pdf() -> bytes:
    """Eine PDF-Datei, die sich nur mit Passwort öffnen lässt."""
    schreiber = PdfWriter()
    schreiber.add_blank_page(width=200, height=200)
    schreiber.encrypt(user_password="geheim", algorithm="RC4-128")
    puffer = io.BytesIO()
    schreiber.write(puffer)
    return puffer.getvalue()


# Jede Datei wird nur einmal gesendet, der Test-Client schließt sie danach.
EINGABEFEHLER = [
    ({"lernziele": (io.BytesIO(b"kein pdf"), "Lernziele.docx")}, "Bitte eine PDF- oder Textdatei"),
    ({"vorlesung": (io.BytesIO(b""), "")}, "Vorlesung: Bitte die PDF-Datei auswählen"),
    ({"lernziele": (io.BytesIO(b""), "")}, "Lernziele: Bitte eine Datei auswählen"),
    ({"lernziele": (io.BytesIO(b""), "leer.pdf")}, "Die Datei ist leer"),
    ({"lernziele": (io.BytesIO(b"%PDF-1.4 kaputt"), "kaputt.pdf")}, "lässt sich nicht lesen"),
    ({"lernziele": (io.BytesIO(b"Kurz."), "kurz.txt")}, "kein lesbarer Text"),
    ({"lernziele": (io.BytesIO(_geschuetzte_pdf()), "geschuetzt.pdf")}, "Passwort geschützt"),
    ({"temperatur": "3"}, "zwischen 0 und 2"),
    ({"temperatur": "warm"}, "keine Zahl"),
    ({"prompt": "zu kurz"}, "mindestens 10 Zeichen"),
    ({"prompt": "x" * 20_001}, "länger als 20000 Zeichen"),
]


@pytest.mark.usefixtures("dienst")
def test_abgelehnter_schluessel(angemeldet: FlaskClient, ki_zustand: KiZustand) -> None:
    """Ein vom Dienst abgelehnter Schlüssel endet mit Fehler und Fehlerkarte."""
    ki_zustand.modus = "401"
    token = abgleich_token(neuer_abgleich(angemeldet))
    assert token is not None
    stand = warten_bis_abgleich_fertig(angemeldet, token)
    assert stand["status"] == "fehler"
    assert "abgelehnt" in (stand["fehler"] or ""), stand
    assert "abgelehnt" in html_von(angemeldet.get(f"/folien/{token}"))


@pytest.mark.usefixtures("dienst")
@pytest.mark.parametrize(("aenderung", "meldung"), EINGABEFEHLER)
def test_eingabefehler(
    app: Flask, angemeldet: FlaskClient, aenderung: dict[str, Any], meldung: str
) -> None:
    """Ungültige Eingaben werden im Formular gemeldet, es entsteht kein Abgleich."""
    assert meldung in html_von(neuer_abgleich(angemeldet, **aenderung))
    assert zahl(app, ZAHL_ABGLEICHE) == 0


@pytest.mark.usefixtures("dienst")
def test_unbekanntes_modell_behaelt_prompt(angemeldet: FlaskClient) -> None:
    """Der Fehler bei einem unbekannten Modell behält den eingegebenen Prompt."""
    antwort = neuer_abgleich(
        angemeldet, prompt="Mein eigener Prompt mit genug Text", modell="gibt-es-nicht"
    )
    html = html_von(antwort)
    assert "Modell aus der Liste" in html
    assert "Mein eigener Prompt" in html


@pytest.mark.usefixtures("laufende", "dienst")
def test_hoechstens_zwei_gleichzeitige_abgleiche(angemeldet: FlaskClient) -> None:
    """Bei zwei laufenden Abgleichen startet kein dritter."""
    assert "Es laufen schon" in html_von(neuer_abgleich(angemeldet))


@pytest.mark.usefixtures("laufende")
def test_verwaister_abgleich_wird_beendet(angemeldet: FlaskClient) -> None:
    """Ein Abgleich ohne Lebenszeichen gilt als abgebrochen."""
    stand = angemeldet.get("/folien/laeuft-2/stand").get_json()
    assert stand["status"] == "fehler"
    assert "Abgebrochen" in stand["fehler"]


@pytest.mark.usefixtures("laufende")
def test_laufender_abgleich_zeigt_fortschritt(angemeldet: FlaskClient) -> None:
    """Die Seite eines laufenden Abgleichs zeigt den Fortschritt."""
    html = html_von(angemeldet.get("/folien/laeuft-0"))
    assert 'data-stand="/folien/laeuft-0/stand"' in html


def test_zu_grosse_datei(
    app: Flask, angemeldet: FlaskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Dateien über der Grenze werden mit 413 abgelehnt."""
    monkeypatch.setitem(app.config, "MAX_CONTENT_LENGTH", 2 * MB)
    # Den Körper im Speicher bauen: Der Test-Client legt große Formulare sonst in
    # einer temporären Datei ab, die er nicht wieder schließt.
    grenze, koerper = encode_multipart(
        {
            "_csrf_token": csrf(angemeldet, "/folien/neu"),
            "vorlesung": FileStorage(io.BytesIO(b"%PDF-" + b"0" * (3 * MB)), "gross.pdf"),
        }
    )
    antwort = angemeldet.post(
        "/folien/neu", data=koerper, content_type=f"multipart/form-data; boundary={grenze}"
    )
    assert antwort.status_code == 413
    assert "größer als 2 MB" in html_von(antwort)


def test_formeln_bleiben_text_im_export(
    app: Flask, angemeldet: FlaskClient, folien_token: str, dienst: FolienDienst
) -> None:
    """Formeln aus der Bildbeschreibung werden im Export nicht ausgeführt."""
    assert dienst.bilder
    ausfuehren(app, "update folien set bildbeschreibung = '=HYPERLINK(\"http://example.org\")'")
    antwort = angemeldet.get(f"/folien/{folien_token}/excel")
    blatt = openpyxl.load_workbook(io.BytesIO(antwort.data))["Folien"]
    zellen = [
        zelle
        for reihe in blatt.iter_rows()
        for zelle in reihe
        if isinstance(zelle.value, str) and zelle.value.startswith("=")
    ]
    assert zellen
    assert all(zelle.data_type == "s" for zelle in zellen)
