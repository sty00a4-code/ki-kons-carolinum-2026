"""Anfragen an den KI-Dienst ohne Netzwerk: Antworten, Ströme und Fehler."""

import io
import json
from dataclasses import dataclass, field
from typing import Any

import pytest
import requests

from app import ki
from app.config import KiEinstellungen

EINSTELLUNGEN = KiEinstellungen(
    url="http://ki.test/v1", schluessel="test-schluessel", max_tokens=500
)
ANFRAGE = ki.Anfrage("modell-a", 0.5, "Ordne die Prüfziele zu.")


@dataclass
class Dienst:
    """Ersetzt requests.post, merkt sich die Anfragen und liefert die gesetzte Antwort."""

    antwort: requests.Response | requests.RequestException = field(
        default_factory=lambda: _antwort(200, b"{}")
    )
    anfragen: list[dict[str, Any]] = field(default_factory=list)

    def __call__(self, url: str, **optionen: Any) -> requests.Response:
        self.anfragen.append({"url": url, **optionen})
        if isinstance(self.antwort, requests.RequestException):
            raise self.antwort
        return self.antwort


class AbreissenderStrom(io.BytesIO):
    """Ein Datenstrom, dessen Verbindung beim Lesen abreißt."""

    def read(self, _groesse: int | None = -1, /) -> bytes:
        """Meldet den Abbruch der Verbindung."""
        raise requests.exceptions.ChunkedEncodingError


def _antwort(status: int, inhalt: bytes, typ: str = "application/json") -> requests.Response:
    antwort = requests.Response()
    antwort.status_code = status
    antwort.headers["content-type"] = typ
    antwort.raw = io.BytesIO(inhalt)
    return antwort


def _strom(*ereignisse: dict[str, Any]) -> requests.Response:
    zeilen = [f"data: {json.dumps(e)}" for e in ereignisse] + [": Kommentar", "data: [DONE]"]
    return _antwort(200, "\n\n".join(zeilen).encode(), "text/event-stream")


def _stueck(text: str, ende: str | None = None) -> dict[str, Any]:
    return {"choices": [{"delta": {"content": text}, "finish_reason": ende}]}


@pytest.fixture(name="dienst")
def fixture_dienst(monkeypatch: pytest.MonkeyPatch) -> Dienst:
    """Der Ersatz für den KI-Dienst."""
    dienst = Dienst()
    monkeypatch.setattr(requests, "post", dienst)
    return dienst


def test_antwort_ohne_strom(dienst: Dienst) -> None:
    """Ohne Zwischenstand wird die vollständige Antwort gelesen."""
    wahl = {"message": {"content": "1.1.1 Karies;X"}, "finish_reason": "stop"}
    dienst.antwort = _antwort(200, json.dumps({"choices": [wahl]}).encode())
    assert ki.abrufen(EINSTELLUNGEN, ANFRAGE) == ki.Antwort("1.1.1 Karies;X", "stop")
    anfrage = dienst.anfragen[0]
    assert anfrage["url"] == "http://ki.test/v1/chat/completions"
    assert anfrage["headers"]["Authorization"] == "Bearer test-schluessel"
    assert anfrage["json"]["max_tokens"] == 500
    assert anfrage["json"]["stream"] is False
    assert [n["role"] for n in anfrage["json"]["messages"]] == ["system", "user"]


def test_strom_mit_zwischenstaenden(dienst: Dienst, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ein Strom liefert Zwischenstände und den Grund für das Ende der Antwort."""
    monkeypatch.setattr(ki, "ZWISCHENSTAND_SEKUNDEN", 0)
    dienst.antwort = _strom(_stueck("Teil 1, "), {"choices": []}, _stueck("Teil 2", "length"))
    zwischenstaende: list[str] = []
    antwort = ki.abrufen(EINSTELLUNGEN, ANFRAGE, zwischenstaende.append)
    assert antwort == ki.Antwort("Teil 1, Teil 2", "length")
    assert zwischenstaende[-1] == "Teil 1, Teil 2"
    assert dienst.anfragen[0]["stream"] is True


def test_fehler_im_strom(dienst: Dienst) -> None:
    """Eine Fehlermeldung im Strom bricht mit der Meldung des Dienstes ab."""
    dienst.antwort = _strom(_stueck("Anfang"), {"error": {"message": "Kontingent erschöpft"}})
    with pytest.raises(ki.KiFehler, match="meldet: Kontingent erschöpft"):
        ki.abrufen(EINSTELLUNGEN, ANFRAGE, lambda _: None)


def test_verbindung_reisst_ab(dienst: Dienst) -> None:
    """Reißt die Verbindung während der Antwort ab, gibt es eine verständliche Meldung."""
    dienst.antwort = _antwort(200, b"", "text/event-stream")
    dienst.antwort.raw = AbreissenderStrom()
    with pytest.raises(ki.KiFehler, match="abgerissen"):
        ki.abrufen(EINSTELLUNGEN, ANFRAGE, lambda _: None)


def test_dienst_nicht_erreichbar(dienst: Dienst) -> None:
    """Ohne Verbindung nennt die Meldung die Art des Fehlers."""
    dienst.antwort = requests.ConnectionError()
    with pytest.raises(ki.KiFehler, match=r"nicht erreichbar \(ConnectionError\)"):
        ki.abrufen(EINSTELLUNGEN, ANFRAGE)


def test_unerwartete_antwort(dienst: Dienst) -> None:
    """Eine Antwort ohne choices gilt als unerwartet."""
    dienst.antwort = _antwort(200, b'{"daten": 1}')
    with pytest.raises(ki.KiFehler, match="unerwartete Antwort"):
        ki.abrufen(EINSTELLUNGEN, ANFRAGE)


@pytest.mark.parametrize(
    ("status", "inhalt", "meldung"),
    [
        (401, b"{}", "Schlüssel abgelehnt (401)"),
        (
            500,
            '{"error": {"message": "Modell überlastet"}}'.encode(),
            "Status 500: Modell überlastet",
        ),
        (502, b"Bad Gateway", "Status 502: Bad Gateway"),
        (400, b'{"error": {"code": 7}}', 'Status 400: {"code": 7}'),
    ],
)
def test_fehlerstatus(dienst: Dienst, status: int, inhalt: bytes, meldung: str) -> None:
    """Fehlerstatus werden mit der Meldung des Dienstes wiedergegeben."""
    dienst.antwort = _antwort(status, inhalt)
    with pytest.raises(ki.KiFehler) as fehler:
        ki.abrufen(EINSTELLUNGEN, ANFRAGE)
    assert meldung in str(fehler.value)


def test_lange_meldungen_werden_gekuerzt(dienst: Dienst) -> None:
    """Meldungen des Dienstes erscheinen höchstens MAX_MELDUNG Zeichen lang."""
    dienst.antwort = _antwort(503, b"x" * 1000, "text/plain")
    with pytest.raises(ki.KiFehler) as fehler:
        ki.abrufen(EINSTELLUNGEN, ANFRAGE)
    assert str(fehler.value).endswith("x" * ki.MAX_MELDUNG)


def test_denkblock_wird_entfernt() -> None:
    """Der Denk-Abschnitt mancher Modelle gehört nicht zur Antwort."""
    assert ki.ohne_denkblock("<think>Zuerst\nüberlegen</think>1.1.1 Karies") == "1.1.1 Karies"
    assert ki.ohne_denkblock(None) == ""


def test_anfrage_ohne_laengengrenze() -> None:
    """Ohne Längengrenze enthält die Anfrage kein max_tokens."""
    assert "max_tokens" not in ANFRAGE.koerper(stream=False)


@pytest.mark.parametrize(
    ("retry_after", "warten"),
    [("7", 7.0), (None, None), ("Wed, 21 Oct 2026 07:28:00 GMT", None), ("-3", None)],
)
def test_zu_viele_anfragen(dienst: Dienst, retry_after: str | None, warten: float | None) -> None:
    """Status 429 liefert die Wartezeit des Dienstes und eine eigene Meldung ohne Kontodaten."""
    dienst.antwort = _antwort(429, b'{"error": {"message": "Limit for user: a@b.de"}}')
    if retry_after:
        dienst.antwort.headers["Retry-After"] = retry_after
    with pytest.raises(ki.KiUeberlastet) as fehler:
        ki.abrufen(EINSTELLUNGEN, ANFRAGE)
    assert fehler.value.warten == warten
    assert "Status 429" in str(fehler.value)
    assert "a@b.de" not in str(fehler.value)
