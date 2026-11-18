"""Vorlesungsabgleich: Excel-Export."""

import io

import openpyxl
import pytest
from flask.testing import FlaskClient
from werkzeug.test import TestResponse


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


def test_angaben_nennen_die_lernziel_datei(export: TestResponse) -> None:
    """Das Blatt Angaben nennt die Lernziel-Datei."""
    mappe = openpyxl.load_workbook(io.BytesIO(export.data))
    angaben = {zeile[0].value: zeile[1].value for zeile in mappe["Angaben"].iter_rows()}
    assert angaben["Abgleich mit"] == "Lernziele (Lernziele_Kapitel_25.pdf)"
