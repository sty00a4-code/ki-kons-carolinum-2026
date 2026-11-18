"""Anfragen an den KI-Dienst über die OpenAI-kompatible Schnittstelle /chat/completions.

abrufen() sendet eine Anfrage und liefert den Text der Antwort. Fehler des
Dienstes, fehlende Verbindungen und unerwartete Antworten werden zu KiFehler
mit einer Meldung für die Oberfläche, zu viele Anfragen (Status 429) zu
KiUeberlastet mit der verlangten Wartezeit.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any

import requests

from .config import KiEinstellungen

SYSTEM = "Du bist ein Dozent der Zahnmedizin"
MAX_TEMPERATUR = 2.0
VERBINDUNGS_TIMEOUT = 15
LESE_TIMEOUT = 300
MAX_MELDUNG = 300

_DENKBLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)

# Ein Text oder eine Liste von Teilen, etwa Text und Bild
Inhalt = str | list[dict[str, Any]]


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

    def koerper(self, *, max_tokens: int | None = None) -> dict[str, Any]:
        """Liefert den JSON-Körper der Anfrage."""
        koerper: dict[str, Any] = {
            "model": self.modell,
            "temperature": self.temperatur,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": self.inhalt},
            ],
        }
        if max_tokens:
            koerper["max_tokens"] = max_tokens
        return koerper


def abrufen(einstellungen: KiEinstellungen, anfrage: Anfrage) -> str:
    """Sendet eine Anfrage und liefert den Text der Antwort."""
    try:
        antwort = requests.post(
            f"{einstellungen.url}/chat/completions",
            json=anfrage.koerper(max_tokens=einstellungen.max_tokens),
            headers={"Authorization": f"Bearer {einstellungen.schluessel}"},
            timeout=(VERBINDUNGS_TIMEOUT, LESE_TIMEOUT),
        )
    except requests.RequestException as exc:
        raise KiFehler(f"Der KI-Dienst ist nicht erreichbar ({type(exc).__name__}).") from exc
    if antwort.status_code == HTTPStatus.TOO_MANY_REQUESTS:
        raise KiUeberlastet(_wartezeit(antwort.headers.get("Retry-After")))
    if antwort.status_code != HTTPStatus.OK:
        raise KiFehler(_fehlertext(antwort))
    try:
        return _antwort_lesen(antwort.json())
    except (ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
        raise KiFehler("Der KI-Dienst hat eine unerwartete Antwort geschickt.") from exc


def ohne_denkblock(text: str | None) -> str:
    """Entfernt den Denkblock <think>...</think>, den manche Modelle voranstellen."""
    return _DENKBLOCK.sub("", text or "")


def _antwort_lesen(daten: Any) -> str:
    text: str = (daten["choices"][0].get("message") or {}).get("content") or ""
    return text


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
