"""Gemeinsame Bausteine der Seiten beider Fachteile."""

from __future__ import annotations

import io
import sqlite3
from collections.abc import Callable

from flask import Response, abort, send_file

from . import excel, hintergrund
from .db import get_db

# Lädt einen Datensatz über sein Token, None, wenn es ihn nicht gibt.
Laden = Callable[[sqlite3.Connection, str], "sqlite3.Row | None"]


def datensatz_oder_404(laden: Laden, token: str) -> sqlite3.Row:
    """Lädt einen Datensatz über sein Token oder bricht mit 404 ab.

    Steht der Datensatz auf "laeuft", werden zuvor verwaiste Durchläufe
    beendet; so zeigt die Seite einen abgebrochenen Durchlauf als Fehler.
    """
    con = get_db()
    datensatz = laden(con, token)
    if datensatz is None:
        abort(404)
    if datensatz["status"] == "laeuft" and hintergrund.verwaiste_beenden(con):
        datensatz = laden(con, token) or datensatz
    return datensatz


def excel_antwort(daten: bytes, dateiname: str) -> Response:
    """Liefert eine Excel-Datei zum Herunterladen."""
    return send_file(
        io.BytesIO(daten), mimetype=excel.MIMETYPE, as_attachment=True, download_name=dateiname
    )
