"""Text aus hochgeladenen Dateien.

Vorlesung und Lernziele kommen als PDF oder Textdatei. Gespeichert wird nur
der extrahierte Text, bei PDFs mit Seitenmarken der Form "[Seite n]".
"""

import io
import logging
import os
import re

from pypdf import PdfReader
from pypdf.errors import PdfReadError

logging.getLogger("pypdf").setLevel(logging.ERROR)

# Obergrenze für alle Texte einer Anfrage, 400.000 Zeichen sind etwa 100.000 Token.
MAX_ZEICHEN = int(os.environ.get("P1_MAX_ZEICHEN", "400000"))
MIN_ZEICHEN = 50


class DokumentFehler(ValueError):
    """Die hochgeladene Datei ist nicht verwendbar."""


def dateiname(datei):
    return os.path.basename((datei.filename or "").replace("\\", "/"))[:120] or "Datei"


def text_aus_upload(datei, bezeichnung):
    """Liefert (Dateiname, Text) einer hochgeladenen PDF- oder Textdatei."""
    name = dateiname(datei)
    daten = datei.read()
    if not daten:
        raise DokumentFehler(f"{bezeichnung}: Die Datei ist leer.")
    if daten[:5] == b"%PDF-":
        text = pdf_text(daten, bezeichnung)
    elif name.lower().endswith((".txt", ".md")):
        text = _dekodieren(daten)
    else:
        raise DokumentFehler(
            f"{bezeichnung}: Bitte eine PDF- oder Textdatei (.txt, .md) hochladen."
        )
    text = aufraeumen(text)
    if len(re.sub(r"\[Seite \d+\]|\s", "", text)) < MIN_ZEICHEN:
        raise DokumentFehler(
            f"{bezeichnung}: In der Datei steht kein lesbarer Text. "
            "Eingescannte PDFs ohne Textebene lassen sich nicht auswerten."
        )
    return name, text


def pdf_text(daten, bezeichnung="PDF"):
    """Liefert den Text einer PDF-Datei mit einer Marke "[Seite n]" je Seite."""
    try:
        leser = PdfReader(io.BytesIO(daten))
        gesperrt = leser.is_encrypted and not leser.decrypt("")
        seiten = [] if gesperrt else [seite.extract_text() or "" for seite in leser.pages]
    except (PdfReadError, ValueError, KeyError, TypeError, OSError) as exc:
        raise DokumentFehler(f"{bezeichnung}: Die PDF-Datei lässt sich nicht lesen.") from exc
    if gesperrt:
        raise DokumentFehler(f"{bezeichnung}: Die PDF-Datei ist mit einem Passwort geschützt.")
    return "\n\n".join(f"[Seite {nr}]\n{text}" for nr, text in enumerate(seiten, 1))


def aufraeumen(text):
    """Entfernt Nullbytes, Leerzeichen am Zeilenende und mehrfache Leerzeilen."""
    text = text.replace("\x00", "").replace("\r\n", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _dekodieren(daten):
    try:
        return daten.decode("utf-8")
    except UnicodeDecodeError:
        return daten.decode("latin-1")
