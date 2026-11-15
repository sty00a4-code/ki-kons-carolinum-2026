"""Vorlesungsabgleich: Excel-Export und Übernahme vorhandener Ergebnisse."""

import io
import json
import re

import openpyxl
import pytest
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from tests.hilfen import abgleich_token, balkenwerte, html_von, uebernehmen


@pytest.fixture(name="export")
def fixture_export(angemeldet: FlaskClient, folien_token: str) -> TestResponse:
    """Der Excel-Export des abgeschlossenen Abgleichs."""
    return angemeldet.get(f"/folien/{folien_token}/excel")


def test_blaetter_des_exports(export: TestResponse) -> None:
    """Der Export hat drei Blätter."""
    mappe = openpyxl.load_workbook(io.BytesIO(export.data))
    assert mappe.sheetnames == ["Folien", "Nach Lernzielen", "Angaben"]


def test_exportzeile_der_folie_zwei(export: TestResponse) -> None:
    """Die Zeile der Folie 2 nennt Lernziele und die unbekannte ID."""
    mappe = openpyxl.load_workbook(io.BytesIO(export.data))
    zeile = [zelle.value for zelle in mappe["Folien"][3]]
    assert zeile[0] == 2, zeile
    assert zeile[2] == "25.1.1.2\n25.9.9.9", zeile
    assert zeile[5] == "nicht in der Liste: 25.9.9.9", zeile


def test_rueckimport_ergibt_dieselben_zahlen(
    angemeldet: FlaskClient, folien_token: str, export: TestResponse
) -> None:
    """Der Reimport des Exports ergibt dieselben Balkenwerte."""
    rueck = abgleich_token(uebernehmen(angemeldet, export.data, "Export.xlsx", titel="Rückimport"))
    assert rueck is not None
    assert balkenwerte(angemeldet, rueck) == balkenwerte(angemeldet, folien_token)


@pytest.mark.usefixtures("folien_token")
def test_json_mit_zaehlung_ab_null(angemeldet: FlaskClient) -> None:
    """Eine JSON-Datei mit Zählung ab 0 wird um 1 verschoben."""
    json_datei = json.dumps(
        [
            {"folien-nr": f"Folien Nr: {i}", "Zuordnung": ["25.3.1.1  "] if i == 0 else []}
            for i in range(4)
        ]
    ).encode()
    antwort = uebernehmen(angemeldet, json_datei, "FolienUndLernzieleZuordnung.json")
    uebernommen = abgleich_token(antwort)
    html = html_von(angemeldet.get(f"/folien/{uebernommen}")) if uebernommen else ""
    assert "Nummern wurden um 1 erhöht" in html
    assert re.search(r'id="folie-1".*?25\.3\.1\.1.*?id="folie-2"', html, re.DOTALL) is not None


@pytest.mark.usefixtures("folien_token")
@pytest.mark.parametrize(
    ("datei", "name", "meldung"),
    [
        (
            json.dumps([{"folien-nr": 9, "Zuordnung": "25.3.1.1"}]).encode(),
            "zu_lang.json",
            "nennt Folie 9",
        ),
        (b"kein json", "kaputt.json", "keine lesbare JSON-Datei"),
    ],
)
def test_ungueltige_uebernahme_abgelehnt(
    angemeldet: FlaskClient, datei: bytes, name: str, meldung: str
) -> None:
    """Zu hohe Foliennummern und unlesbare Dateien werden abgelehnt."""
    assert meldung in html_von(uebernehmen(angemeldet, datei, name))
