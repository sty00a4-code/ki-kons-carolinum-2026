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

from app import db, pruefziele
from app.pruefziele import Liste
from tests.hilfen import (
    MB,
    KiZustand,
    ausfuehren,
    csrf,
    html_von,
    modellantwort,
    neue_zuordnung,
    token_aus,
    warten_bis_fertig,
    zahl,
)


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
    ({"vorlesung": (io.BytesIO(b""), "")}, "Vorlesung: Bitte eine Datei auswählen"),
    ({"lernziele": (io.BytesIO(b""), "")}, "Lernziele: Bitte eine Datei auswählen"),
    ({"lernziele": (io.BytesIO(b""), "leer.pdf")}, "Die Datei ist leer"),
    ({"lernziele": (io.BytesIO(b"%PDF-1.4 kaputt"), "kaputt.pdf")}, "lässt sich nicht lesen"),
    ({"lernziele": (io.BytesIO(b"Kurz."), "kurz.txt")}, "kein lesbarer Text"),
    ({"lernziele": (io.BytesIO(_geschuetzte_pdf()), "geschuetzt.pdf")}, "Passwort geschützt"),
    ({"temperatur": "3"}, "zwischen 0 und 2"),
    ({"temperatur": "warm"}, "keine Zahl"),
    ({"prompt": "zu kurz"}, "mindestens 10 Zeichen"),
    ({"prompt": "x" * 20_001}, "länger als 20000 Zeichen"),
    ({"liste": "gibt-es-nicht"}, "Prüfziel-Liste aus der Auswahl"),
]


def test_abgelehnter_schluessel(angemeldet: FlaskClient, ki_zustand: KiZustand) -> None:
    """Ein vom Dienst abgelehnter Schlüssel endet mit Fehler und Fehlerkarte."""
    ki_zustand.modus = "401"
    token = token_aus(neue_zuordnung(angemeldet))
    assert token is not None
    stand = warten_bis_fertig(angemeldet, token)
    assert stand["status"] == "fehler"
    assert "abgelehnt" in (stand["fehler"] or ""), stand
    assert "fehlgeschlagen" in html_von(angemeldet.get(f"/ergebnisse/{token}"))


def test_abgeschnittene_antwort_wird_gemeldet(
    angemeldet: FlaskClient, ki_zustand: KiZustand, liste: Liste
) -> None:
    """Eine wegen der Längengrenze abgeschnittene Antwort wird gemeldet."""
    ki_zustand.modus = "length"
    ki_zustand.antwort = modellantwort(liste)
    token = token_aus(neue_zuordnung(angemeldet))
    assert token is not None
    stand = warten_bis_fertig(angemeldet, token)
    html = html_von(angemeldet.get(f"/ergebnisse/{token}"))
    assert stand["status"] == "fertig"
    assert "Längengrenze" in html
    assert "Ohne Zeile in der Antwort:" in html


@pytest.mark.usefixtures("ki_zustand")
@pytest.mark.parametrize(("aenderung", "meldung"), EINGABEFEHLER)
def test_eingabefehler(
    app: Flask, angemeldet: FlaskClient, aenderung: dict[str, Any], meldung: str
) -> None:
    """Ungültige Eingaben werden im Formular gemeldet, es entsteht keine Zuordnung."""
    assert meldung in html_von(neue_zuordnung(angemeldet, **aenderung))
    assert zahl(app, "select count(*) from auswertungen") == 0


@pytest.mark.usefixtures("ki_zustand")
def test_unbekanntes_modell_behaelt_prompt(angemeldet: FlaskClient) -> None:
    """Der Fehler bei einem unbekannten Modell behält den eingegebenen Prompt."""
    antwort = neue_zuordnung(
        angemeldet, prompt="Mein eigener Prompt mit genug Text", modell="gibt-es-nicht"
    )
    html = html_von(antwort)
    assert "Modell aus der Liste" in html
    assert "Mein eigener Prompt" in html


@pytest.mark.usefixtures("laufende", "ki_zustand")
def test_hoechstens_zwei_gleichzeitige_durchlaeufe(angemeldet: FlaskClient) -> None:
    """Bei zwei laufenden Durchläufen startet kein dritter."""
    assert "Es laufen schon" in html_von(neue_zuordnung(angemeldet))


@pytest.mark.usefixtures("laufende")
def test_verwaister_durchlauf_wird_beendet(angemeldet: FlaskClient) -> None:
    """Ein Durchlauf ohne Lebenszeichen gilt als abgebrochen."""
    stand = angemeldet.get("/ergebnisse/laeuft-2/stand").get_json()
    assert stand["status"] == "fehler"
    assert "Abgebrochen" in stand["fehler"]


@pytest.mark.usefixtures("laufende")
def test_laufender_durchlauf_zeigt_fortschritt(angemeldet: FlaskClient) -> None:
    """Die Seite eines laufenden Durchlaufs zeigt den Fortschritt."""
    html = html_von(angemeldet.get("/ergebnisse/laeuft-0"))
    assert 'data-stand="/ergebnisse/laeuft-0/stand"' in html


def test_zu_grosse_datei(
    app: Flask, angemeldet: FlaskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Dateien über der Grenze werden mit 413 abgelehnt."""
    monkeypatch.setitem(app.config, "MAX_CONTENT_LENGTH", 2 * MB)
    # Den Körper im Speicher bauen: Der Test-Client legt große Formulare sonst in
    # einer temporären Datei ab, die er nicht wieder schließt.
    grenze, koerper = encode_multipart(
        {
            "_csrf_token": csrf(angemeldet, "/neu"),
            "vorlesung": FileStorage(io.BytesIO(b"%PDF-" + b"0" * (3 * MB)), "gross.pdf"),
        }
    )
    antwort = angemeldet.post(
        "/neu", data=koerper, content_type=f"multipart/form-data; boundary={grenze}"
    )
    assert antwort.status_code == 413
    assert "größer als 2 MB" in html_von(antwort)


def test_formeln_bleiben_text_im_export(app: Flask, angemeldet: FlaskClient) -> None:
    """Formeln aus der Antwort werden im Export nicht ausgeführt."""
    zeit = db.jetzt()
    ausfuehren(
        app,
        "insert into auswertungen (token, titel, modell, pruefziele_liste, quelle, status, "
        "rohantwort, erstellt_am, aktualisiert_am) "
        "values ('formel', 'Formel', 'm', ?, 'import', 'fertig', ?, ?, ?)",
        (
            pruefziele.STANDARD,
            '1.1.1 Karies;X;=HYPERLINK("http://example.org");25.1.1.1',
            zeit,
            zeit,
        ),
    )
    antwort = angemeldet.get("/ergebnisse/formel/excel")
    blatt = openpyxl.load_workbook(io.BytesIO(antwort.data))["Zuordnung"]
    zellen = [
        zelle
        for reihe in blatt.iter_rows()
        for zelle in reihe
        if isinstance(zelle.value, str) and zelle.value.startswith("=")
    ]
    assert zellen
    assert all(zelle.data_type == "s" for zelle in zellen)
