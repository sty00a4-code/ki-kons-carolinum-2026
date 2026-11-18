"""Anmeldung, CSRF-Schutz und Zugriffsschutz der Seiten."""

import re
from typing import NoReturn

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.folien import speicher
from tests.hilfen import PASSWORT, anmelden, csrf

GESCHUETZT = [
    "/",
    "/folien/",
    "/folien/neu",
    "/folien/abc",
    "/folien/abc/stand",
    "/folien/abc/excel",
    "/folien/abc/vorlesung.pdf",
]
SEITEN = ["/folien/", "/folien/neu"]


@pytest.mark.parametrize("pfad", GESCHUETZT)
def test_ohne_login_zur_anmeldung(client: FlaskClient, pfad: str) -> None:
    """Ohne Anmeldung leitet jede Seite zum Login."""
    antwort = client.get(pfad)
    assert antwort.status_code == 302
    assert "/login" in antwort.headers["Location"]


def test_login_ohne_csrf_token_abgelehnt(client: FlaskClient) -> None:
    """Ein Login ohne CSRF-Token wird mit 400 abgelehnt."""
    antwort = client.post("/login", data={"username": "doktorand1", "password": "x"})
    assert antwort.status_code == 400


def test_falsches_passwort_meldet_fehler(client: FlaskClient) -> None:
    """Ein falsches Passwort zeigt eine Fehlermeldung."""
    antwort = anmelden(client, "falsch")
    assert "Login fehlgeschlagen" in antwort.get_data(as_text=True)


def test_login_mit_richtigem_passwort(client: FlaskClient) -> None:
    """Mit dem richtigen Passwort leitet der Login weiter."""
    assert anmelden(client, PASSWORT).status_code == 302


def test_formular_ohne_csrf_token_abgelehnt(angemeldet: FlaskClient) -> None:
    """Ein Formular ohne CSRF-Token wird abgelehnt."""
    assert angemeldet.post("/folien/neu", data={"prompt": "x"}).status_code == 400


@pytest.mark.parametrize("pfad", SEITEN)
def test_seiten_laden_nach_login(angemeldet: FlaskClient, pfad: str) -> None:
    """Nach dem Login laden alle Seiten."""
    assert angemeldet.get(pfad).status_code == 200


@pytest.mark.parametrize("pfad", ["", "/stand", "/excel", "/vorlesung.pdf", "/folie/1.jpg"])
def test_unbekannter_abgleich_ergibt_404(angemeldet: FlaskClient, pfad: str) -> None:
    """Ein unbekanntes Token ergibt 404."""
    assert angemeldet.get(f"/folien/gibt-es-nicht{pfad}").status_code == 404


def test_sicherheits_header(angemeldet: FlaskClient) -> None:
    """HTML-Seiten erlauben nur eigene Skripte und Styles und lassen sich nicht einbetten."""
    antwort = angemeldet.get("/folien/neu")
    richtlinie = antwort.headers["Content-Security-Policy"]
    assert "script-src 'self';" in richtlinie
    assert "style-src 'self';" in richtlinie
    assert "unsafe" not in richtlinie
    assert "frame-ancestors 'none'" in richtlinie
    assert antwort.headers["X-Content-Type-Options"] == "nosniff"
    assert antwort.headers["X-Frame-Options"] == "DENY"
    with angemeldet.get("/static/seiten.js") as skript:
        assert skript.headers["X-Content-Type-Options"] == "nosniff"
        assert "Content-Security-Policy" not in skript.headers


def test_seiten_ohne_eingebettete_skripte(angemeldet: FlaskClient) -> None:
    """Die Seiten binden nur das Modul seiten.js ein und enthalten kein eigenes Skript."""
    for pfad in SEITEN:
        html = angemeldet.get(pfad).get_data(as_text=True)
        assert html.count("<script") == 1, pfad
        assert 'type="module" src="/static/seiten.js"' in html, pfad
        assert not re.search(r"\son[a-z]+=", html), pfad


def test_seiten_ohne_inline_styles(angemeldet: FlaskClient, folien_token: str) -> None:
    """Auch Seiten mit Balken kommen ohne Inline-Styles aus, die Breite steht in data-breite."""
    mit_balken = ["/folien/", f"/folien/{folien_token}?ansicht=ziele"]
    for pfad in [*SEITEN, *mit_balken, f"/folien/{folien_token}"]:
        html = angemeldet.get(pfad).get_data(as_text=True)
        assert not re.search(r"\sstyle=|<style", html), pfad
        if pfad in mit_balken:
            assert re.search(r'data-breite="\d+(\.\d+)?(%|px)"', html), pfad


def test_csrf_token_mit_umlauten(client: FlaskClient) -> None:
    """Ein CSRF-Token mit Umlauten wird abgelehnt, ohne dass der Server abstürzt."""
    client.get("/login")
    antwort = client.post("/login", data={"username": "x", "password": "y", "_csrf_token": "ä"})
    assert antwort.status_code == 400


def test_unbekannter_login(client: FlaskClient) -> None:
    """Ein unbekannter Benutzer erhält dieselbe Meldung wie ein falsches Passwort."""
    daten = {"username": "niemand", "password": "x", "_csrf_token": csrf(client, "/login")}
    assert "Login fehlgeschlagen" in client.post("/login", data=daten).get_data(as_text=True)


def test_abmelden(angemeldet: FlaskClient) -> None:
    """Nach dem Abmelden führt jede Seite wieder zum Login."""
    antwort = angemeldet.post("/logout", data={"_csrf_token": csrf(angemeldet, "/folien/neu")})
    assert antwort.headers["Location"].endswith("/login")
    assert "/login" in angemeldet.get("/folien/neu").headers["Location"]


def test_startseite_nach_login(angemeldet: FlaskClient) -> None:
    """Angemeldet führt die Startseite zum Formular für einen neuen Abgleich."""
    assert angemeldet.get("/").headers["Location"].endswith("/folien/neu")


def test_interner_fehler_zeigt_fehlerseite(
    app: Flask, angemeldet: FlaskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ein unerwarteter Fehler ergibt Status 500 mit eigener Fehlerseite."""

    def abbrechen(*_args: object) -> NoReturn:
        raise RuntimeError

    app.config["PROPAGATE_EXCEPTIONS"] = False
    monkeypatch.setattr(speicher, "alle", abbrechen)
    antwort = angemeldet.get("/folien/")
    assert antwort.status_code == 500
    assert "Fehler auf dem Server" in antwort.get_data(as_text=True)
