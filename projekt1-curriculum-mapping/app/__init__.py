"""Curriculum-Mapping: Vorlesungsfolien mit Lernzielen oder Prüfzielen abgleichen.

create_app() baut die Anwendung. Die Datenbank liegt unter data/, der
Sitzungsschlüssel unter instance/, die Einstellungen kommen aus
Umgebungsvariablen (siehe config).
"""

from __future__ import annotations

import secrets
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from flask import Flask, current_app, redirect, render_template, session, url_for
from flask.typing import ResponseReturnValue
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

from . import config, db, formate, hintergrund, security
from .auth import bp as auth_bp
from .folien.routes import bp as folien_bp
from .folien.speicher import MAX_TITEL

SCHLUESSEL_BYTES = 32


def create_app(test_config: Mapping[str, Any] | None = None) -> Flask:
    """Baut die Anwendung; test_config ergänzt oder ersetzt die Konfiguration."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(config.flask_konfiguration())
    app.config["DATABASE"] = str(db.STANDARD_PFAD)
    if test_config:
        app.config.update(test_config)
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = sitzungsschluessel(Path(app.instance_path) / "secret_key")
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    hintergrund.einrichten(app)
    app.before_request(security.csrf_pruefen)
    app.after_request(security.kopfzeilen_setzen)
    for blueprint in (auth_bp, folien_bp):
        app.register_blueprint(blueprint)

    app.register_error_handler(RequestEntityTooLarge, _zu_gross)
    app.register_error_handler(400, _ungueltig)
    app.register_error_handler(404, _nicht_gefunden)
    app.register_error_handler(500, _interner_fehler)
    app.context_processor(_vorlagenwerte)
    for filter_funktion in (formate.datum, formate.zahl, formate.temperatur, formate.anzahl):
        app.add_template_filter(filter_funktion)
    app.add_url_rule("/", "index", _startseite)
    return app


def sitzungsschluessel(pfad: Path) -> bytes:
    """Liest den Sitzungsschlüssel oder legt ihn an, lesbar nur für den Besitzer."""
    if pfad.exists():
        return pfad.read_bytes()
    schluessel = secrets.token_bytes(SCHLUESSEL_BYTES)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.touch(mode=0o600)
    pfad.write_bytes(schluessel)
    return schluessel


def _vorlagenwerte() -> dict[str, object]:
    ki = config.ki_einstellungen()
    return {
        "csrf_token": security.csrf_token,
        "ki_bereit": ki.bereit,
        "modell_name": ki.modell_name,
        "max_titel": MAX_TITEL,
    }


def _startseite() -> ResponseReturnValue:
    if session.get("user_id"):
        return redirect(url_for("folien.neu"))
    return redirect(url_for("auth.login"))


def _fehlerseite(titel: str, meldung: str, status: int) -> ResponseReturnValue:
    return render_template("fehler.html", titel=titel, meldung=meldung), status


def _zu_gross(_fehler: RequestEntityTooLarge) -> ResponseReturnValue:
    grenze = current_app.config["MAX_CONTENT_LENGTH"] // config.MB
    return _fehlerseite("Upload zu groß", f"Die Dateien sind zusammen größer als {grenze} MB.", 413)


def _ungueltig(fehler: HTTPException) -> ResponseReturnValue:
    return _fehlerseite("Anfrage ungültig", fehler.description or "", 400)


def _nicht_gefunden(_fehler: HTTPException) -> ResponseReturnValue:
    return _fehlerseite(
        "Nicht gefunden", "Diese Seite oder dieses Ergebnis gibt es nicht (mehr).", 404
    )


def _interner_fehler(_fehler: Exception) -> ResponseReturnValue:
    return _fehlerseite(
        "Fehler auf dem Server",
        "Die Anfrage ließ sich nicht bearbeiten. Der Fehler ist protokolliert.",
        500,
    )
