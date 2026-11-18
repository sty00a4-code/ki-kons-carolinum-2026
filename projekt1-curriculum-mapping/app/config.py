"""Einstellungen der Anwendung aus Umgebungsvariablen.

P1_LLM_URL          Basis-URL des KI-Dienstes (OpenAI-kompatibel)
P1_LLM_API_KEY      Schlüssel für den KI-Dienst, ohne ihn startet kein Durchlauf
P1_LLM_MODELLE      Modellauswahl als "modell-id=Anzeigename,..."
P1_LLM_BILDMODELLE  Modelle für Bildbeschreibungen, gleiches Format
P1_LLM_MAX_TOKENS   Obergrenze für die Länge einer Antwort
P1_MAX_UPLOAD_MB    Obergrenze für alle Dateien eines Formulars in MB
P1_MAX_ZEICHEN      Obergrenze für alle Texte eines Abgleichs
P1_MAX_FOLIEN       Obergrenze für die Seitenzahl einer Vorlesung
COOKIE_SECURE       1, wenn die Anwendung hinter HTTPS läuft
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

from flask import Flask, current_app

MB = 1024 * 1024

STANDARD_URL = "https://litellm.s.studiumdigitale.uni-frankfurt.de/v1"

# Ein Modell als Paar aus ID und Anzeigename
Modell = tuple[str, str]

STANDARD_MODELLE: tuple[Modell, ...] = (
    ("mistral-large-3-675b-instruct-2512", "Mistral Large 3"),
    ("qwen3-235b-a22b", "Qwen3 235B"),
    ("openai-gpt-oss-120b", "GPT-OSS 120B"),
    ("qwen3-30b-a3b-instruct-2507", "Qwen3 30B"),
)
STANDARD_BILDMODELLE: tuple[Modell, ...] = (("qwen3-omni-30b-a3b-instruct", "Qwen3 Omni 30B"),)


@dataclass(frozen=True)
class KiEinstellungen:
    """Zugang zum KI-Dienst und Auswahl der Modelle."""

    url: str = STANDARD_URL
    schluessel: str = ""
    modelle: tuple[Modell, ...] = STANDARD_MODELLE
    bildmodelle: tuple[Modell, ...] = STANDARD_BILDMODELLE
    max_tokens: int | None = None

    @property
    def bereit(self) -> bool:
        """Gibt an, ob ein Schlüssel für den KI-Dienst hinterlegt ist."""
        return bool(self.schluessel)

    def modell_name(self, modell_id: str) -> str:
        """Liefert den Anzeigenamen eines Modells, unbekannte IDs unverändert."""
        return dict(self.modelle + self.bildmodelle).get(modell_id, modell_id)

    @classmethod
    def aus_umgebung(cls, umgebung: Mapping[str, str]) -> KiEinstellungen:
        """Liest die Einstellungen aus Umgebungsvariablen."""
        grenze = umgebung.get("P1_LLM_MAX_TOKENS", "").strip()
        return cls(
            url=umgebung.get("P1_LLM_URL", STANDARD_URL).strip().rstrip("/"),
            schluessel=umgebung.get("P1_LLM_API_KEY", "").strip(),
            modelle=_modelle(umgebung.get("P1_LLM_MODELLE", "")) or STANDARD_MODELLE,
            bildmodelle=_modelle(umgebung.get("P1_LLM_BILDMODELLE", "")) or STANDARD_BILDMODELLE,
            max_tokens=int(grenze) if grenze.isdigit() else None,
        )


@dataclass(frozen=True)
class Grenzen:
    """Obergrenzen für Uploads, Texte und Foliensätze."""

    upload_mb: int = 80
    zeichen: int = 400_000
    folien: int = 200

    @classmethod
    def aus_umgebung(cls, umgebung: Mapping[str, str]) -> Grenzen:
        """Liest die Obergrenzen aus Umgebungsvariablen."""
        return cls(
            upload_mb=_ganzzahl(umgebung, "P1_MAX_UPLOAD_MB", cls.upload_mb),
            zeichen=_ganzzahl(umgebung, "P1_MAX_ZEICHEN", cls.zeichen),
            folien=_ganzzahl(umgebung, "P1_MAX_FOLIEN", cls.folien),
        )


def flask_konfiguration(umgebung: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Liefert die Konfiguration für Flask, ohne Datenbankpfad und Sitzungsschlüssel."""
    umgebung = os.environ if umgebung is None else umgebung
    obergrenzen = Grenzen.aus_umgebung(umgebung)
    return {
        "KI": KiEinstellungen.aus_umgebung(umgebung),
        "GRENZEN": obergrenzen,
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_COOKIE_SECURE": umgebung.get("COOKIE_SECURE", "") == "1",
        # Foliensätze als PDF sind oft größer als 30 MB.
        "MAX_CONTENT_LENGTH": obergrenzen.upload_mb * MB,
        # Grenze für Textfelder wie den Prompt (Flask-Standard: 500 KB)
        "MAX_FORM_MEMORY_SIZE": 2 * MB,
    }


def ki_einstellungen(app: Flask | None = None) -> KiEinstellungen:
    """Liefert die Einstellungen des KI-Dienstes der angegebenen oder der laufenden App."""
    return cast(KiEinstellungen, (app or current_app).config["KI"])


def grenzen(app: Flask | None = None) -> Grenzen:
    """Liefert die Obergrenzen der angegebenen oder der laufenden App."""
    return cast(Grenzen, (app or current_app).config["GRENZEN"])


def _modelle(text: str) -> tuple[Modell, ...]:
    """Liest eine Modellauswahl der Form "id=Name,id2=Name2", Namen sind optional."""
    paare = []
    for teil in text.split(","):
        modell_id, _, name = teil.partition("=")
        if modell_id.strip():
            paare.append((modell_id.strip(), name.strip() or modell_id.strip()))
    return tuple(paare)


def _ganzzahl(umgebung: Mapping[str, str], variable: str, standard: int) -> int:
    wert = umgebung.get(variable, "").strip()
    return int(wert) if wert.isdigit() and int(wert) > 0 else standard
