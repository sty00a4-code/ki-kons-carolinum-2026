"""Text aus hochgeladenen PDF- und Textdateien.

Bei PDFs steht vor dem Text jeder Seite eine Marke der Form "[Seite n]".
Eingescannte PDFs ohne Textebene und geschützte PDFs werden abgelehnt.
"""

from __future__ import annotations

import io
import logging
import os
import re
from typing import NamedTuple

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from .fehler import EingabeFehler

logging.getLogger("pypdf").setLevel(logging.ERROR)

MIN_ZEICHEN = 50
MAX_DATEINAME = 120
PDF_KENNUNG = b"%PDF-"
TEXTENDUNGEN = (".txt", ".md")

_SEITENMARKE = re.compile(r"\[Seite \d+\]")


class DokumentFehler(EingabeFehler):
    """Die hochgeladene Datei ist nicht verwendbar."""


class Textdatei(NamedTuple):
    """Name und gelesener Text einer hochgeladenen Datei."""

    name: str
    text: str


def dateiname(roh: str | None) -> str:
    """Liefert den Dateinamen ohne Pfad, höchstens MAX_DATEINAME Zeichen lang."""
    return os.path.basename((roh or "").replace("\\", "/"))[:MAX_DATEINAME] or "Datei"


def ist_pdf(daten: bytes) -> bool:
    """Prüft die Kennung am Anfang einer PDF-Datei."""
    return daten.startswith(PDF_KENNUNG)


def text_lesen(name: str, daten: bytes, bezeichnung: str) -> str:
    """Liefert den aufgeräumten Text einer PDF- oder Textdatei.

    bezeichnung steht vor jeder Fehlermeldung, etwa "Lernziele".
    """
    if not daten:
        raise DokumentFehler(f"{bezeichnung}: Die Datei ist leer.")
    if ist_pdf(daten):
        text = pdf_text(daten, bezeichnung)
    elif name.lower().endswith(TEXTENDUNGEN):
        text = _dekodieren(daten)
    else:
        raise DokumentFehler(
            f"{bezeichnung}: Bitte eine PDF- oder Textdatei (.txt, .md) hochladen."
        )
    text = aufraeumen(text)
    if len(re.sub(r"\s", "", _SEITENMARKE.sub("", text))) < MIN_ZEICHEN:
        raise DokumentFehler(
            f"{bezeichnung}: In der Datei steht kein lesbarer Text. "
            "Eingescannte PDFs ohne Textebene lassen sich nicht auswerten."
        )
    return text


def pdf_text(daten: bytes, bezeichnung: str = "PDF") -> str:
    """Liefert den Text einer PDF-Datei mit einer Marke "[Seite n]" je Seite."""
    seiten = seitentexte(daten, bezeichnung)
    return "\n\n".join(f"[Seite {nr}]\n{text}" for nr, text in enumerate(seiten, 1))


def seitentexte(daten: bytes, bezeichnung: str = "PDF") -> list[str]:
    """Liefert den Text jeder Seite einer PDF-Datei."""
    try:
        leser = PdfReader(io.BytesIO(daten))
        gesperrt = leser.is_encrypted and not leser.decrypt("")
        seiten = [] if gesperrt else [seite.extract_text() or "" for seite in leser.pages]
    except (PdfReadError, ValueError, KeyError, TypeError, OSError) as exc:
        raise DokumentFehler(f"{bezeichnung}: Die PDF-Datei lässt sich nicht lesen.") from exc
    if gesperrt:
        raise DokumentFehler(f"{bezeichnung}: Die PDF-Datei ist mit einem Passwort geschützt.")
    return seiten


def aufraeumen(text: str) -> str:
    """Entfernt Nullbytes, Leerzeichen am Zeilenende und mehrfache Leerzeilen."""
    text = text.replace("\x00", "").replace("\r\n", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _dekodieren(daten: bytes) -> str:
    try:
        return daten.decode("utf-8")
    except UnicodeDecodeError:
        return daten.decode("latin-1")
