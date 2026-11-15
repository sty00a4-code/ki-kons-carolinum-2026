"""Hintergrund-Durchläufe: Start, Ende, Fehler im Thread, Sperre beim Anlegen, Zeitstempel."""

import logging
import sqlite3
import threading
from contextlib import closing
from typing import Any, NoReturn

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import formate, hintergrund, ki
from app.db import get_db
from app.fehler import EingabeFehler
from app.folien import lauf
from tests.hilfen import (
    FolienDienst,
    KiZustand,
    abfragen,
    abgleich_token,
    ausfuehren,
    csrf,
    hintergrund_beenden,
    html_von,
    neue_zuordnung,
    neuer_abgleich,
    token_aus,
    warten_bis_abgleich_fertig,
    warten_bis_fertig,
)


def _nichts_speichern(_app: Flask, _kennung: int, _meldung: str) -> None:
    """Fehler werden in diesen Tests nicht gespeichert."""


@pytest.mark.usefixtures("dienst")
def test_unerwarteter_fehler_beendet_den_abgleich(
    angemeldet: FlaskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ein unerwarteter Fehler im Thread wird am Abgleich gespeichert."""

    def abbrechen(*_args: object) -> NoReturn:
        raise RuntimeError

    monkeypatch.setattr(lauf, "_folien_bearbeiten", abbrechen)
    token = abgleich_token(neuer_abgleich(angemeldet))
    assert token is not None
    stand = warten_bis_abgleich_fertig(angemeldet, token)
    assert stand["status"] == "fehler"
    assert "Unerwarteter Fehler (RuntimeError)." in stand["fehler"]


@pytest.mark.parametrize(
    ("wert", "erwartet"),
    [("2026-11-16T09:05:00", "16.11.2026, 09:05"), ("kein Datum", "kein Datum"), (None, "")],
)
def test_datum(wert: str | None, erwartet: str) -> None:
    """Zeitstempel erscheinen deutsch formatiert, andere Werte unverändert."""
    assert formate.datum(wert) == erwartet


@pytest.mark.usefixtures("ki_zustand")
def test_unerwarteter_fehler_beendet_die_zuordnung(
    angemeldet: FlaskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Auch eine Zuordnung endet nach einem unerwarteten Fehler mit Meldung."""

    def abbrechen(*_args: object) -> NoReturn:
        raise RuntimeError

    monkeypatch.setattr(ki, "abrufen", abbrechen)
    token = token_aus(neue_zuordnung(angemeldet))
    assert token is not None
    stand = warten_bis_fertig(angemeldet, token)
    assert stand["status"] == "fehler"
    assert stand["fehler"] == "Unerwarteter Fehler (RuntimeError)."


def test_derselbe_durchlauf_startet_nur_einmal(app: Flask) -> None:
    """Solange ein Durchlauf arbeitet, lehnt die Verwaltung einen zweiten Start ab."""
    gestartet, weiter = threading.Event(), threading.Event()

    def arbeiten(_app: Flask, _kennung: int) -> None:
        gestartet.set()
        weiter.wait(5)

    verwaltung = hintergrund.Hintergrund(app)
    durchlauf = hintergrund.Durchlauf("test", 1, arbeiten, _nichts_speichern)
    thread = verwaltung.starten(durchlauf)
    try:
        assert gestartet.wait(5)
        assert verwaltung.laeuft("test", 1)
        with pytest.raises(RuntimeError, match="arbeitet schon"):
            verwaltung.starten(durchlauf)
    finally:
        weiter.set()
        thread.join(5)
    assert not verwaltung.laeuft("test", 1)


@pytest.mark.usefixtures("ki_zustand")
def test_von_aussen_beendete_zuordnung_bleibt_beendet(
    app: Flask, angemeldet: FlaskClient, ki_zustand: KiZustand, caplog: pytest.LogCaptureFixture
) -> None:
    """Endet eine Zuordnung während der Antwort, überschreibt der Durchlauf nichts mehr."""

    def beenden(_body: object) -> str:
        ausfuehren(app, "update auswertungen set status = 'fehler', fehler = 'Beendet'")
        return "Antwort " * 200

    ki_zustand.antwort_fuer = beenden
    caplog.set_level(logging.INFO)
    token = token_aus(neue_zuordnung(angemeldet))
    hintergrund_beenden()
    zeile = abfragen(
        app, "select status, fehler, rohantwort from auswertungen where token = ?", (token,)
    )[0]
    assert tuple(zeile) == ("fehler", "Beendet", "")
    assert "beendet, er läuft nicht mehr" in caplog.text


def test_geloeschter_abgleich_fragt_nicht_weiter(
    app: Flask, angemeldet: FlaskClient, ki_zustand: KiZustand, dienst: FolienDienst
) -> None:
    """Nach dem Löschen eines Abgleichs gehen keine Anfragen mehr an den KI-Dienst."""

    def antworten_und_loeschen(body: dict[str, Any]) -> str | None:
        text = dienst(body)
        if dienst.folien == [1, 2]:
            ausfuehren(app, "delete from folienabgleiche")
        return text

    ki_zustand.antwort_fuer = antworten_und_loeschen
    neuer_abgleich(angemeldet, bildmodell="")
    hintergrund_beenden()
    assert dienst.folien == [1, 2]


def test_platz_pruefen_sperrt_bis_zum_commit(app: Flask) -> None:
    """Zwischen Prüfung und Commit kann keine andere Verbindung einen Durchlauf anlegen."""
    with app.app_context(), closing(sqlite3.connect(app.config["DATABASE"], timeout=0)) as andere:
        con = get_db()
        hintergrund.platz_pruefen(con)
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            andere.execute("begin immediate")
        con.commit()
        andere.execute("begin immediate")
        andere.rollback()


@pytest.mark.usefixtures("laufende")
def test_volle_plaetze_geben_die_sperre_frei(app: Flask) -> None:
    """Ist kein Platz frei, endet die Transaktion mit der Fehlermeldung."""
    with app.app_context():
        con = get_db()
        with pytest.raises(EingabeFehler, match="Es laufen schon"):
            hintergrund.platz_pruefen(con)
        assert not con.in_transaction


def test_abgleich_wird_nur_einmal_fortgesetzt(
    app: Flask, angemeldet: FlaskClient, dienst: FolienDienst, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Setzt eine andere Anfrage den Abgleich zugleich fort, startet kein zweiter Thread."""
    dienst.fehler_bei = 3
    token = abgleich_token(neuer_abgleich(angemeldet, bildmodell=""))
    assert token is not None
    assert warten_bis_abgleich_fertig(angemeldet, token)["status"] == "fehler"
    formular = {"_csrf_token": csrf(angemeldet, f"/folien/{token}")}
    gestartet: list[int] = []

    def andere_anfrage_war_schneller(_kennung: int) -> bool:
        ausfuehren(app, "update folienabgleiche set status = 'laeuft' where token = ?", (token,))
        return False

    monkeypatch.setattr(lauf, "laeuft", andere_anfrage_war_schneller)
    monkeypatch.setattr(lauf, "starten", gestartet.append)
    antwort = angemeldet.post(f"/folien/{token}/fortsetzen", data=formular, follow_redirects=True)
    assert "inzwischen schon fortgesetzt" in html_von(antwort)
    assert not gestartet
