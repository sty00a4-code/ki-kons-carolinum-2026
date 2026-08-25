"""Flask App-Factory. Registriert Sicherheits-Middleware und Blueprints."""

import os
import secrets

from flask import Flask, abort, redirect, request, session, url_for

from . import db, security


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    # Echte Daten liegen unter data/ (git-ignoriert), nie im Repo.
    data_dir = os.path.join(os.path.dirname(app.root_path), "data")
    os.makedirs(data_dir, exist_ok=True)

    app.config.update(
        DATABASE=os.path.join(data_dir, "leistung.db"),
        SECRET_KEY=_load_or_create_secret(app),
        SESSION_COOKIE_HTTPONLY=True,  # Cookie nicht per JS lesbar
        SESSION_COOKIE_SAMESITE="Lax",  # CSRF-Grundschutz
        # Hinter HTTPS (VPS/Caddy): COOKIE_SECURE=1 setzen, lokal bleibt es aus.
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "") == "1",
    )

    db.init_app(app)

    from .auth import bp as auth_bp
    from .routes_analysis import bp as analysis_bp
    from .routes_doktorand import bp as doktorand_bp
    from .routes_faelle import bp as faelle_bp
    from .routes_student import bp as student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(doktorand_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(faelle_bp)

    @app.before_request
    def _csrf_protect():
        if request.method == "POST" and not security.check_csrf(
            request.form.get("_csrf_token", "")
        ):
            abort(400, "CSRF-Token ungültig oder fehlt.")

    @app.context_processor
    def _inject_globals():
        ctx = {"csrf_token": security.csrf_token}
        # Bot-Daten NUR für den eingeloggten Studierenden (eigene Daten).
        if session.get("role") == "student" and session.get("student_id"):
            from .student_stats import bot_context

            try:
                ctx["bot_data"] = bot_context(db.get_db(), session["student_id"])
            except Exception:
                ctx["bot_data"] = None
        # Lehrenden-Bot: Kohorten-Daten (Klarnamen – sieht der Doktorand überall).
        elif session.get("role") in ("doktorand", "admin"):
            from .matching import kohorten_context

            try:
                ctx["bot_data_lehrende"] = kohorten_context(db.get_db())
            except Exception:
                ctx["bot_data_lehrende"] = None
        return ctx

    @app.route("/ablauf")
    @security.login_required
    def ablauf():
        from flask import render_template

        return render_template("ablauf.html")

    @app.route("/")
    def index():
        role = session.get("role")
        if role == "student":
            return redirect(url_for("student.meine"))
        if role in ("doktorand", "admin"):
            return redirect(url_for("doktorand.liste"))
        return redirect(url_for("auth.login"))

    return app


def _load_or_create_secret(app):
    """Persistenter, git-ignorierter Secret-Key (instance/secret_key)."""
    path = os.path.join(app.instance_path, "secret_key")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    key = secrets.token_bytes(32)
    with open(path, "wb") as f:
        f.write(key)
    return key
