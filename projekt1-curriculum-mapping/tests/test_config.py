"""Einstellungen aus Umgebungsvariablen."""

from pathlib import Path

import pytest

from app import SCHLUESSEL_BYTES, create_app, sitzungsschluessel
from app.config import (
    MB,
    STANDARD_BILDMODELLE,
    Grenzen,
    KiEinstellungen,
    flask_konfiguration,
    grenzen,
    ki_einstellungen,
)


def test_ki_einstellungen_aus_umgebung() -> None:
    """URL, Schlüssel, Modelle und Längengrenze werden gelesen und bereinigt."""
    ki = KiEinstellungen.aus_umgebung(
        {
            "P1_LLM_URL": " https://ki.example.org/v1/ ",
            "P1_LLM_API_KEY": " test-schluessel ",
            "P1_LLM_MODELLE": "modell-a=Modell A, modell-b ,",
            "P1_LLM_MAX_TOKENS": "4000",
        }
    )
    assert ki.url == "https://ki.example.org/v1"
    assert ki.bereit
    assert ki.modelle == (("modell-a", "Modell A"), ("modell-b", "modell-b"))
    assert ki.bildmodelle == STANDARD_BILDMODELLE
    assert ki.max_tokens == 4000
    assert ki.modell_name("modell-a") == "Modell A"
    assert ki.modell_name("unbekannt") == "unbekannt"


def test_ki_einstellungen_ohne_angaben() -> None:
    """Ohne Umgebungsvariablen gelten die Vorgaben, ohne Schlüssel startet nichts."""
    ki = KiEinstellungen.aus_umgebung({"P1_LLM_MAX_TOKENS": "viele"})
    assert ki == KiEinstellungen()
    assert not ki.bereit


@pytest.mark.parametrize(
    ("wert", "erwartet"), [("", 80), ("0", 80), ("-5", 80), ("x", 80), ("12", 12)]
)
def test_ungueltige_grenzen_ergeben_die_vorgabe(wert: str, erwartet: int) -> None:
    """Nur positive ganze Zahlen ersetzen die Vorgabe."""
    assert Grenzen.aus_umgebung({"P1_MAX_UPLOAD_MB": wert}).upload_mb == erwartet


def test_flask_konfiguration() -> None:
    """Upload-Grenze und sichere Cookies folgen der Umgebung."""
    werte = flask_konfiguration({"P1_MAX_UPLOAD_MB": "10", "COOKIE_SECURE": "1"})
    assert werte["MAX_CONTENT_LENGTH"] == 10 * MB
    assert werte["SESSION_COOKIE_SECURE"] is True
    assert werte["SESSION_COOKIE_HTTPONLY"] is True
    assert flask_konfiguration({})["SESSION_COOKIE_SECURE"] is False


def test_app_liest_die_umgebung(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """create_app() übernimmt die Einstellungen aus den Umgebungsvariablen."""
    monkeypatch.setenv("P1_LLM_API_KEY", "test-schluessel")
    monkeypatch.setenv("P1_MAX_FOLIEN", "20")
    app = create_app({"DATABASE": str(tmp_path / "test.db"), "SECRET_KEY": "test-sitzung"})
    assert ki_einstellungen(app).bereit
    assert grenzen(app).folien == 20


def test_sitzungsschluessel_wird_einmal_angelegt(tmp_path: Path) -> None:
    """Der Schlüssel entsteht beim ersten Start und ist nur für den Besitzer lesbar."""
    pfad = tmp_path / "instance" / "secret_key"
    schluessel = sitzungsschluessel(pfad)
    assert len(schluessel) == SCHLUESSEL_BYTES
    assert pfad.stat().st_mode & 0o777 == 0o600
    assert sitzungsschluessel(pfad) == schluessel
