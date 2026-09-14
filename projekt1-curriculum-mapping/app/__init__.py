"""Curriculum-Mapping: Zuordnung von Prüfzielen zu Lernzielen (Kategorie 1).

Die Datenbank liegt unter data/, der Sitzungsschlüssel unter instance/.
"""

import os
import secrets

from flask import Flask, abort, redirect, render_template, request, session, url_for
from werkzeug.exceptions import RequestEntityTooLarge

from . import auswertungen, db, formate, ki_dienst, security
from .auth import bp as auth_bp
from .routes import bp as zuordnung_bp

MB = 1024 * 1024


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    data_dir = os.path.join(os.path.dirname(app.root_path), "data")
    os.makedirs(data_dir, exist_ok=True)

    app.config.update(
        DATABASE=os.path.join(data_dir, "projekt1.db"),
        SECRET_KEY=_load_or_create_secret(app),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        # Hinter HTTPS COOKIE_SECURE=1 setzen.
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "") == "1",
        # Foliensätze als PDF sind oft größer als 30 MB.
        MAX_CONTENT_LENGTH=int(os.environ.get("P1_MAX_UPLOAD_MB", "80")) * MB,
        # Grenze für Textfelder wie den Prompt (Flask-Standard: 500 KB).
        MAX_FORM_MEMORY_SIZE=2 * MB,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(zuordnung_bp)

    @app.before_request
    def _csrf_protect():
        if request.method == "POST" and not security.check_csrf(
            request.form.get("_csrf_token", "")
        ):
            abort(
                400,
                "Das Formular ist abgelaufen (CSRF-Token fehlt oder ist ungültig). "
                "Bitte die Seite neu laden und noch einmal senden.",
            )

    @app.errorhandler(RequestEntityTooLarge)
    def _zu_gross(_exc):
        grenze = app.config["MAX_CONTENT_LENGTH"] // MB
        meldung = f"Die Dateien sind zusammen größer als {grenze} MB."
        return render_template("fehler.html", titel="Upload zu groß", meldung=meldung), 413

    @app.errorhandler(400)
    def _ungueltig(exc):
        return render_template(
            "fehler.html", titel="Anfrage ungültig", meldung=exc.description
        ), 400

    @app.errorhandler(404)
    def _nicht_gefunden(_exc):
        meldung = "Diese Seite oder dieses Ergebnis gibt es nicht (mehr)."
        return render_template("fehler.html", titel="Nicht gefunden", meldung=meldung), 404

    @app.context_processor
    def _inject_globals():
        return {
            "csrf_token": security.csrf_token,
            "ki_bereit": ki_dienst.bereit(),
            "modell_name": ki_dienst.modell_name,
            "max_titel": auswertungen.MAX_TITEL,
        }

    app.add_template_filter(formate.datum)
    app.add_template_filter(formate.zahl)
    app.add_template_filter(formate.temperatur)
    app.add_template_filter(formate.anzahl)

    @app.route("/")
    def index():
        if session.get("user_id"):
            return redirect(url_for("zuordnung.neu"))
        return redirect(url_for("auth.login"))

    return app


def _load_or_create_secret(app):
    """Liest den Sitzungsschlüssel aus instance/secret_key oder legt ihn an."""
    path = os.path.join(app.instance_path, "secret_key")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    key = secrets.token_bytes(32)
    with open(path, "wb") as f:
        f.write(key)
    return key
