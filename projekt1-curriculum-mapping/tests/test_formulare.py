"""Prüfung der Eingaben im Formular einer neuen Zuordnung, Übernahme und Vergleich."""

import io
from typing import Any

import openpyxl
import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.config import Grenzen
from app.zuordnung.routes import MAX_VERGLEICH
from tests.hilfen import MODELL, Lauf, ausfuehren, csrf, html_von, neue_zuordnung, zahl

ZAHL_AUSWERTUNGEN = "select count(*) from auswertungen"


@pytest.mark.usefixtures("ki_zustand")
def test_textdatei_in_latin_1(app: Flask, angemeldet: FlaskClient) -> None:
    """Textdateien dürfen auch in Latin-1 kodiert sein."""
    text = "25.1.1.1 Erkrankungen erkennen und in der Therapieplanung berücksichtigen. 2\n"
    lernziele = (io.BytesIO(text.encode("latin-1") * 2), "lernziele.txt")
    assert neue_zuordnung(angemeldet, lernziele=lernziele).status_code == 302
    assert zahl(app, ZAHL_AUSWERTUNGEN) == 1


@pytest.mark.usefixtures("ki_zustand")
def test_zu_lange_texte(app: Flask, angemeldet: FlaskClient) -> None:
    """Die Texte einer Zuordnung dürfen zusammen nicht zu lang werden."""
    app.config["GRENZEN"] = Grenzen(zeichen=100)
    assert "Die Texte sind zusammen" in html_von(neue_zuordnung(angemeldet))
    assert zahl(app, ZAHL_AUSWERTUNGEN) == 0


def _excel_mit_zwei_blaettern() -> bytes:
    mappe = openpyxl.Workbook()
    erstes = mappe.active
    assert erstes is not None
    for blatt in (erstes, mappe.create_sheet()):
        blatt.append(["Prüfziele", "Abdeckung", "Begründung", "Lernziel-ID"])
        blatt.append(["1.1.1 Karies", "X", "Wird behandelt.", "25.1.1.1"])
    erstes.title, mappe.worksheets[1].title = "mistral 0.0", "mistral 1.0"
    puffer = io.BytesIO()
    mappe.save(puffer)
    return puffer.getvalue()


def _excel_uebernehmen(client: FlaskClient, daten: bytes, **ueberschreiben: str) -> str:
    werte: dict[str, Any] = {
        "_csrf_token": csrf(client, "/import"),
        "modell": MODELL,
        "liste": "orale-medizin",
        "titel": "",
        "prompt": "",
        "excel": (io.BytesIO(daten), "Auswertung.xlsx"),
    }
    werte.update(ueberschreiben)
    antwort = client.post("/import", data=werte, content_type="multipart/form-data")
    return html_von(client.get(antwort.headers["Location"])) if antwort.status_code == 302 else ""


def test_uebernahme_mehrerer_blaetter(app: Flask, angemeldet: FlaskClient) -> None:
    """Jedes Blatt wird ein Ergebnis; die Meldung nennt alle Blätter."""
    html = _excel_uebernehmen(angemeldet, _excel_mit_zwei_blaettern())
    assert "2 Blätter übernommen: mistral 0.0 (1 Zeilen), mistral 1.0 (1 Zeilen)." in html
    assert zahl(app, ZAHL_AUSWERTUNGEN) == 2


def test_uebernahme_ohne_modell(app: Flask, angemeldet: FlaskClient) -> None:
    """Ohne Angabe des Modells wird nichts übernommen."""
    werte = {
        "_csrf_token": csrf(angemeldet, "/import"),
        "modell": "",
        "liste": "orale-medizin",
        "excel": (io.BytesIO(_excel_mit_zwei_blaettern()), "Auswertung.xlsx"),
    }
    antwort = angemeldet.post("/import", data=werte, content_type="multipart/form-data")
    assert "welches Modell die Excel-Datei erzeugt hat" in html_von(antwort)
    assert zahl(app, ZAHL_AUSWERTUNGEN) == 0


def test_unbekannte_ansicht_zeigt_die_tabelle(angemeldet: FlaskClient, ergebnis_token: str) -> None:
    """Eine unbekannte Ansicht fällt auf die Tabelle zurück."""
    html = html_von(angemeldet.get(f"/ergebnisse/{ergebnis_token}?ansicht=gibt-es-nicht"))
    assert "data-filterbereich" in html


@pytest.mark.usefixtures("ki_zustand")
def test_wiederholen_ohne_lernziele(app: Flask, angemeldet: FlaskClient, durchlauf: Lauf) -> None:
    """Ohne gespeicherte Lernziel-Datei lässt sich ein Ergebnis nicht wiederholen."""
    ausfuehren(app, "update auswertungen set lernziele_name = null, lernziele_text = null")
    antwort = angemeldet.post(
        f"/ergebnisse/{durchlauf.token}/wiederholen",
        data={
            "_csrf_token": csrf(angemeldet, "/neu"),
            "modell": MODELL,
            "temperatur": "0",
            "prompt": "Ordne die Lernziele den Prüfzielen zu.",
        },
    )
    assert "keine Lernziel-Datei gespeichert" in html_von(antwort)


def test_vergleich_prueft_die_auswahl(angemeldet: FlaskClient, ergebnis_token: str) -> None:
    """Zu viele, unbekannte oder einzelne Ergebnisse ergeben eine Meldung oder 404."""
    zu_viele = "&".join(f"t={nr}" for nr in range(MAX_VERGLEICH + 1))
    assert "höchstens" in html_von(angemeldet.get(f"/vergleich?{zu_viele}"))
    assert angemeldet.get("/vergleich?t=gibt-es-nicht").status_code == 404
    assert "mindestens 2" in html_von(angemeldet.get(f"/vergleich?t={ergebnis_token}"))
    aendern = angemeldet.get(f"/vergleich?t={ergebnis_token}&aendern=1")
    assert "mindestens 2" not in html_von(aendern)


def test_unbekannte_pruefziel_liste(angemeldet: FlaskClient) -> None:
    """Eine unbekannte Prüfziel-Liste ergibt 404."""
    assert angemeldet.get("/pruefziele?liste=gibt-es-nicht").status_code == 404
