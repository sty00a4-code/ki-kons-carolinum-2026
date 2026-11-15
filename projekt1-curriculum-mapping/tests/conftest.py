"""Gemeinsame Fixtures: Anwendung mit eigener Datenbank, Testserver und fertige Läufe."""

import threading
from collections.abc import Iterator
from pathlib import Path

import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.security import generate_password_hash

from app import create_app, db, ki, pruefziele
from app.config import KiEinstellungen
from app.folien import lauf as folien_lauf
from app.pruefziele import Liste
from tests.hilfen import (
    API_SCHLUESSEL,
    BENUTZER,
    LERNZIEL_ANTWORTEN,
    PASSWORT,
    FolienDienst,
    KiServer,
    KiZustand,
    Lauf,
    abgleich_token,
    anmelden,
    ausfuehren,
    hintergrund_beenden,
    modellantwort,
    neue_zuordnung,
    neuer_abgleich,
    token_aus,
    warten_bis_abgleich_fertig,
    warten_bis_fertig,
)

KI_VARIABLEN = (
    "P1_LLM_URL",
    "P1_LLM_API_KEY",
    "P1_LLM_MODELLE",
    "P1_LLM_BILDMODELLE",
    "P1_LLM_MAX_TOKENS",
)


@pytest.fixture(name="saubere_umgebung", autouse=True)
def fixture_saubere_umgebung(monkeypatch: pytest.MonkeyPatch) -> None:
    """Entfernt die KI-Einstellungen aus der Umgebung und verkürzt die Wartezeiten."""
    for variable in KI_VARIABLEN:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setattr(ki, "ZWISCHENSTAND_SEKUNDEN", 0)
    monkeypatch.setattr(folien_lauf, "WIEDERHOLEN_NACH_SEKUNDEN", 0)
    monkeypatch.setattr(folien_lauf, "WARTEN_BEI_UEBERLASTUNG", 0)


@pytest.fixture(name="liste", scope="session")
def fixture_liste() -> Liste:
    """Die Standardliste der Prüfziele."""
    return pruefziele.liste()


@pytest.fixture(name="ki_server", scope="session")
def fixture_ki_server() -> Iterator[KiServer]:
    """Lokaler Testserver, der den KI-Dienst nachahmt."""
    server = KiServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.fixture(name="ki_zustand")
def fixture_ki_zustand(app: Flask, ki_server: KiServer) -> KiZustand:
    """Richtet die Anwendung auf den Testserver aus und setzt dessen Zustand zurück."""
    ki_server.zustand.zuruecksetzen()
    app.config["KI"] = KiEinstellungen(url=ki_server.url, schluessel=API_SCHLUESSEL)
    return ki_server.zustand


@pytest.fixture(name="app")
def fixture_app(tmp_path: Path) -> Iterator[Flask]:
    """Frische Anwendung mit leerer Datenbank und einem Benutzer."""
    anwendung = create_app(
        {"DATABASE": str(tmp_path / "test.db"), "SECRET_KEY": "test-sitzung", "TESTING": True}
    )
    ausfuehren(
        anwendung,
        "insert into users (username, password_hash, role) values (?, ?, 'doktorand')",
        (BENUTZER, generate_password_hash(PASSWORT, method="pbkdf2:sha256:1000")),
    )
    yield anwendung
    hintergrund_beenden()


@pytest.fixture(name="client")
def fixture_client(app: Flask) -> FlaskClient:
    """Test-Client ohne Anmeldung."""
    return app.test_client()


@pytest.fixture(name="angemeldet")
def fixture_angemeldet(client: FlaskClient) -> FlaskClient:
    """Test-Client mit angemeldetem Benutzer."""
    assert anmelden(client).status_code == 302
    return client


@pytest.fixture(name="durchlauf")
def fixture_durchlauf(angemeldet: FlaskClient, ki_zustand: KiZustand, liste: Liste) -> Lauf:
    """Eine abgeschlossene Zuordnung gegen den Testserver."""
    ki_zustand.antwort = modellantwort(liste)
    token = token_aus(neue_zuordnung(angemeldet))
    stand = warten_bis_fertig(angemeldet, token) if token else {}
    return Lauf(token, stand, [anfrage.body for anfrage in ki_zustand.anfragen])


@pytest.fixture(name="ergebnis_token")
def fixture_ergebnis_token(durchlauf: Lauf) -> str:
    """Das Token der abgeschlossenen Zuordnung."""
    assert durchlauf.token is not None
    return durchlauf.token


@pytest.fixture(name="dienst")
def fixture_dienst(ki_zustand: KiZustand) -> FolienDienst:
    """Antworten des Testservers für den Vorlesungsabgleich."""
    folien_dienst = FolienDienst(LERNZIEL_ANTWORTEN)
    ki_zustand.antwort_fuer = folien_dienst
    return folien_dienst


@pytest.fixture(name="abgleich")
def fixture_abgleich(angemeldet: FlaskClient, dienst: FolienDienst) -> Lauf:
    """Ein abgeschlossener Vorlesungsabgleich mit Lernzielen."""
    token = abgleich_token(neuer_abgleich(angemeldet))
    stand = warten_bis_abgleich_fertig(angemeldet, token) if token else {}
    return Lauf(token, stand, list(dienst.bodies))


@pytest.fixture(name="folien_token")
def fixture_folien_token(abgleich: Lauf) -> str:
    """Das Token des abgeschlossenen Abgleichs."""
    assert abgleich.token is not None
    return abgleich.token


@pytest.fixture(name="laufende")
def fixture_laufende(app: Flask) -> None:
    """Zwei aktuelle und ein verwaister Durchlauf in der Datenbank."""
    jetzt, alt = db.jetzt(), db.vor_minuten(60)
    for nr, zeit in enumerate([jetzt, jetzt, alt]):
        ausfuehren(
            app,
            "insert into auswertungen (token, titel, modell, pruefziele_liste, quelle, "
            "status, erstellt_am, aktualisiert_am) "
            "values (?, 'Test', 'm', ?, 'ki', 'laeuft', ?, ?)",
            (f"laeuft-{nr}", pruefziele.STANDARD, zeit, zeit),
        )
