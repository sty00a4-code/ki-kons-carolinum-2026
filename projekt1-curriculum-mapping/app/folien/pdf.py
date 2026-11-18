"""Folien einer Vorlesung aus der PDF-Datei: Text und gerenderte Bilder."""

from __future__ import annotations

import io
import threading
from typing import NamedTuple

import pypdfium2 as pdfium

from .. import dokumente
from ..dokumente import DokumentFehler

# Längere Seite der Bilder in Pixel und Qualität der JPEG-Kompression
VORSCHAU_PIXEL = 480
VORSCHAU_QUALITAET = 80
MODELL_PIXEL = 1280
MODELL_QUALITAET = 85

# pdfium ist nicht threadsicher, deshalb laufen alle Aufrufe nacheinander.
_PDFIUM = threading.Lock()


class Seite(NamedTuple):
    """Text und Vorschaubild (JPEG) einer Seite."""

    text: str
    vorschau: bytes


def seiten_lesen(daten: bytes, max_seiten: int, bezeichnung: str = "Vorlesung") -> list[Seite]:
    """Liefert Text und Vorschaubild jeder Seite einer PDF-Datei."""
    if not dokumente.ist_pdf(daten):
        raise DokumentFehler(f"{bezeichnung}: Bitte den Foliensatz als PDF hochladen.")
    texte = [dokumente.aufraeumen(t) for t in dokumente.seitentexte(daten, bezeichnung)]
    if not texte:
        raise DokumentFehler(f"{bezeichnung}: Die PDF-Datei hat keine Seiten.")
    if len(texte) > max_seiten:
        raise DokumentFehler(
            f"{bezeichnung}: Die PDF-Datei hat {len(texte)} Seiten, erlaubt sind {max_seiten}. "
            "Bitte nur ein Kapitel hochladen."
        )
    with _PDFIUM:
        try:
            pdf = pdfium.PdfDocument(daten)
        except pdfium.PdfiumError as exc:
            raise DokumentFehler(
                f"{bezeichnung}: Die PDF-Datei lässt sich nicht darstellen."
            ) from exc
        try:
            bilder = [
                _jpeg(pdf, nr, VORSCHAU_PIXEL, VORSCHAU_QUALITAET) for nr in range(1, len(pdf) + 1)
            ]
        finally:
            pdf.close()
    if len(bilder) != len(texte):
        raise DokumentFehler(f"{bezeichnung}: Die PDF-Datei ist beschädigt.")
    return [Seite(text, bild) for text, bild in zip(texte, bilder, strict=True)]


def seitenbild(daten: bytes, nr: int) -> bytes:
    """Liefert Seite nr (ab 1) als JPEG in der Größe für das Bildmodell."""
    with _PDFIUM:
        pdf = pdfium.PdfDocument(daten)
        try:
            return _jpeg(pdf, nr, MODELL_PIXEL, MODELL_QUALITAET)
        finally:
            pdf.close()


def _jpeg(pdf: pdfium.PdfDocument, nr: int, pixel: int, qualitaet: int) -> bytes:
    seite = pdf[nr - 1]
    try:
        massstab = pixel / max(seite.get_size())
        bild = seite.render(scale=massstab).to_pil().convert("RGB")
    finally:
        seite.close()
    puffer = io.BytesIO()
    bild.save(puffer, "JPEG", quality=qualitaet, optimize=True)
    return puffer.getvalue()
