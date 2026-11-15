"""Anfragen an den KI-Dienst über die OpenAI-kompatible Schnittstelle /chat/completions.

abrufen() sendet eine Anfrage und liefert den Text der Antwort. Mit einer
Rückruffunktion für Zwischenstände läuft die Anfrage gestreamt. Fehler des
Dienstes, abgerissene Verbindungen und unerwartete Antworten werden zu
KiFehler mit einer Meldung für die Oberfläche, zu viele Anfragen (Status 429)
zu KiUeberlastet mit der verlangten Wartezeit.
"""

from __future__ import annotations

import json
import re
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any

import requests

from .config import KiEinstellungen

SYSTEM = "Du bist ein Dozent der Zahnmedizin"
MAX_TEMPERATUR = 2.0
VERBINDUNGS_TIMEOUT = 15
LESE_TIMEOUT = 300
# Abstand, in dem ein gestreamter Durchlauf seinen Zwischenstand meldet
ZWISCHENSTAND_SEKUNDEN = 3
MAX_MELDUNG = 300

_DENKBLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)

# Ein Text oder eine Liste von Teilen, etwa Text und Bild
Inhalt = str | list[dict[str, Any]]
Zwischenstand = Callable[[str], None]


class KiFehler(RuntimeError):
    """Fehler bei einer Anfrage an den KI-Dienst, die Meldung ist für die Oberfläche bestimmt."""


class KiUeberlastet(KiFehler):
    """Der KI-Dienst nimmt vorübergehend keine Anfragen an (Status 429).

    warten ist die Wartezeit in Sekunden aus dem Header Retry-After, sonst None.
    Die Meldung des Dienstes wird nicht übernommen, sie nennt oft das Konto.
    """

    def __init__(self, warten: float | None) -> None:
        super().__init__(
            "Der KI-Dienst nimmt gerade keine weiteren Anfragen an (Status 429). "
            "Bitte später erneut versuchen."
        )
        self.warten = warten


@dataclass(frozen=True)
class Anfrage:
    """Eine Nutzernachricht an ein Modell, die Systemrolle ergänzt koerper()."""

    modell: str
    temperatur: float | None
    inhalt: Inhalt

    def koerper(self, *, stream: bool, max_tokens: int | None = None) -> dict[str, Any]:
        """Liefert den JSON-Körper der Anfrage."""
        koerper: dict[str, Any] = {
            "model": self.modell,
            "temperature": self.temperatur,
            "stream": stream,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": self.inhalt},
            ],
        }
        if max_tokens:
            koerper["max_tokens"] = max_tokens
        return koerper


@dataclass(frozen=True)
class Antwort:
    """Text einer Antwort und der Grund für ihr Ende (finish_reason), etwa "length"."""

    text: str
    abbruch: str | None = None


def abrufen(
    einstellungen: KiEinstellungen,
    anfrage: Anfrage,
    zwischenstand: Zwischenstand | None = None,
) -> Antwort:
    """Sendet eine Anfrage und liefert die Antwort.

    Mit zwischenstand läuft die Anfrage gestreamt; die Funktion erhält dann
    alle ZWISCHENSTAND_SEKUNDEN den bisher empfangenen Text.
    """
    stream = zwischenstand is not None
    try:
        antwort = requests.post(
            f"{einstellungen.url}/chat/completions",
            json=anfrage.koerper(stream=stream, max_tokens=einstellungen.max_tokens),
            headers={"Authorization": f"Bearer {einstellungen.schluessel}"},
            stream=stream,
            timeout=(VERBINDUNGS_TIMEOUT, LESE_TIMEOUT),
        )
    except requests.RequestException as exc:
        raise KiFehler(f"Der KI-Dienst ist nicht erreichbar ({type(exc).__name__}).") from exc
    with antwort:
        if antwort.status_code == HTTPStatus.TOO_MANY_REQUESTS:
            raise KiUeberlastet(_wartezeit(antwort.headers.get("Retry-After")))
        if antwort.status_code != HTTPStatus.OK:
            raise KiFehler(_fehlertext(antwort))
        try:
            if "text/event-stream" in antwort.headers.get("content-type", ""):
                return _strom_lesen(antwort, zwischenstand)
            return _antwort_lesen(antwort.json())
        except requests.RequestException as exc:
            raise KiFehler(
                f"Die Verbindung zum KI-Dienst ist abgerissen ({type(exc).__name__})."
            ) from exc
        except (ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
            raise KiFehler("Der KI-Dienst hat eine unerwartete Antwort geschickt.") from exc


def ohne_denkblock(text: str | None) -> str:
    """Entfernt den Denkblock <think>...</think>, den manche Modelle voranstellen."""
    return _DENKBLOCK.sub("", text or "")


def _antwort_lesen(daten: Any) -> Antwort:
    wahl = daten["choices"][0]
    return Antwort((wahl.get("message") or {}).get("content") or "", wahl.get("finish_reason"))


def _strom_lesen(antwort: requests.Response, zwischenstand: Zwischenstand | None) -> Antwort:
    teile: list[str] = []
    abbruch = None
    zuletzt = time.monotonic()
    for stueck in _ereignisse(antwort):
        for wahl in stueck.get("choices") or []:
            teile.append((wahl.get("delta") or {}).get("content") or "")
            abbruch = wahl.get("finish_reason") or abbruch
        if zwischenstand and time.monotonic() - zuletzt >= ZWISCHENSTAND_SEKUNDEN:
            zwischenstand("".join(teile))
            zuletzt = time.monotonic()
    return Antwort("".join(teile), abbruch)


def _ereignisse(antwort: requests.Response) -> Iterator[dict[str, Any]]:
    """Liefert die Daten der Server-Sent Events bis zur Marke [DONE]."""
    antwort.encoding = "utf-8"
    for zeile in antwort.iter_lines(decode_unicode=True):
        if not zeile or not zeile.startswith("data:"):
            continue
        daten = zeile.removeprefix("data:").strip()
        if daten == "[DONE]":
            return
        stueck = json.loads(daten)
        if stueck.get("error"):
            raise KiFehler(f"Der KI-Dienst meldet: {_kurz(stueck['error'])}")
        yield stueck


def _fehlertext(antwort: requests.Response) -> str:
    if antwort.status_code in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
        return f"Der KI-Dienst hat den Schlüssel abgelehnt ({antwort.status_code})."
    try:
        daten = antwort.json()
    except ValueError:
        daten = None
    fehler = daten.get("error") if isinstance(daten, dict) else None
    meldung = _kurz(fehler or antwort.text)
    return f"Der KI-Dienst antwortet mit Status {antwort.status_code}: {meldung}"


def _wartezeit(retry_after: str | None) -> float | None:
    """Sekunden aus Retry-After; die Angabe als Datum wird nicht ausgewertet."""
    wert = (retry_after or "").strip()
    return float(wert) if wert.isdigit() else None


def _kurz(fehler: object) -> str:
    if isinstance(fehler, dict):
        fehler = fehler.get("message") or json.dumps(fehler, ensure_ascii=False)
    return str(fehler).strip()[:MAX_MELDUNG]
