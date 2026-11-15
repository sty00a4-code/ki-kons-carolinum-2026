"""Excel-Export einer Zuordnung und Reimport über /import."""

import io

import openpyxl
import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from app import pruefziele
from app.pruefziele import Liste
from app.zuordnung.auswertung import auswerten
from app.zuordnung.excel_import import temperatur_aus_name
from tests.hilfen import LERNZIELE_PDF, MODELL, abfragen, csrf, html_von, token_aus


@pytest.fixture(name="export")
def fixture_export(angemeldet: FlaskClient, ergebnis_token: str) -> TestResponse:
    """Der Excel-Export des abgeschlossenen Durchlaufs."""
    return angemeldet.get(f"/ergebnisse/{ergebnis_token}/excel")


@pytest.fixture(name="rueckimport")
def fixture_rueckimport(angemeldet: FlaskClient, export: TestResponse) -> TestResponse:
    """Antwort auf den Reimport des Exports."""
    return angemeldet.post(
        "/import",
        data={
            "_csrf_token": csrf(angemeldet, "/import"),
            "excel": (io.BytesIO(export.data), "Export.xlsx"),
            "lernziele": (io.BytesIO(LERNZIELE_PDF), "Lernziele_Kapitel_25.pdf"),
            "modell": MODELL,
            "liste": pruefziele.STANDARD,
            "titel": "Rückimport",
            "prompt": "",
        },
        content_type="multipart/form-data",
    )


def test_export_ist_ein_download(export: TestResponse) -> None:
    """Der Export wird als Datei zum Herunterladen ausgeliefert."""
    assert export.status_code == 200
    assert "attachment" in export.headers.get("Content-Disposition", "")


def test_blaetter_und_spalten_im_export(export: TestResponse) -> None:
    """Der Export hat drei Blätter und die erwarteten Spalten."""
    mappe = openpyxl.load_workbook(io.BytesIO(export.data))
    assert mappe.sheetnames == ["Zuordnung", "Nach Lernzielen", "Angaben"]
    kopf = [zelle.value for zelle in mappe["Zuordnung"][1]]
    assert kopf[:5] == ["Teil", "Prüfziel", "Abdeckung", "Begründung", "Lernziel-ID (Kapitel)"]


def test_rueckimport_leitet_zum_ergebnis(rueckimport: TestResponse) -> None:
    """Der Reimport eines Blatts leitet zum neuen Ergebnis."""
    assert token_aus(rueckimport) is not None, rueckimport.status_code


def _zuordnung_von(
    app: Flask, token: str, liste: Liste
) -> list[tuple[str | None, int, list[str], str]]:
    """Liest die gespeicherte Antwort eines Ergebnisses als Liste von Zeilenmerkmalen."""
    zeile = abfragen(app, "select * from auswertungen where token = ?", (token,))[0]
    ergebnis = auswerten(zeile["rohantwort"], liste, zeile["lernziele_text"])
    return [
        ((z.eintrag or {}).get("schluessel"), z.stufe, z.lernziele, z.begruendung)
        for z in ergebnis.zeilen
    ]


def test_rueckimport_ergibt_dieselbe_zuordnung(
    app: Flask, ergebnis_token: str, rueckimport: TestResponse, liste: Liste
) -> None:
    """Der Reimport liefert dieselbe Zuordnung und den Titel mit Zusatz."""
    rueck = token_aus(rueckimport)
    assert rueck is not None
    assert _zuordnung_von(app, ergebnis_token, liste) == _zuordnung_von(app, rueck, liste)
    titel = abfragen(app, "select titel from auswertungen where token = ?", (rueck,))[0][0]
    assert titel == "Rückimport · Zuordnung"


def test_vergleich_mit_sich_selbst_ergibt_kappa_eins(
    angemeldet: FlaskClient, ergebnis_token: str, rueckimport: TestResponse
) -> None:
    """Der Vergleich von Original und Reimport zeigt Kappa 1."""
    rueck = token_aus(rueckimport)
    antwort = angemeldet.get(f"/vergleich?t={ergebnis_token}&t={rueck}")
    assert antwort.status_code == 200
    assert "<strong>1,00</strong>" in html_von(antwort)


@pytest.mark.parametrize(
    ("name", "erwartet"),
    [
        ("mistral 1.0", 1.0),
        ("mistal 0.5", 0.5),
        ("Temp 0,7", 0.7),
        ("Temperatur: 1", 1.0),
        ("temp1", 1.0),
        ("Tabelle1", None),
        ("Sheet2", None),
        ("Lauf 1", None),
        ("Version 1.2.3", None),
        ("Temp 3", None),
        ("", None),
        (None, None),
    ],
)
def test_temperatur_aus_blattname(name: str | None, erwartet: float | None) -> None:
    """Nur eine Zahl nach "Temp" oder eine Dezimalzahl gilt als Temperatur."""
    assert temperatur_aus_name(name) == erwartet
