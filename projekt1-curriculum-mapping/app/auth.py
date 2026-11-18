"""Anmeldung und Abmeldung."""

from __future__ import annotations

import functools
import secrets

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask.typing import ResponseReturnValue
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login() -> ResponseReturnValue:
    """Anmeldeseite; nach erfolgreicher Anmeldung geht es zur Startseite."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_db().execute("select * from users where username = ?", (username,)).fetchone()
        # Auch ohne Benutzer wird ein Passwort geprüft, damit die Antwortzeit nichts verrät.
        passwort_hash = user["password_hash"] if user else _platzhalter_hash()
        if check_password_hash(passwort_hash, password) and user:
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["username"] = user["username"]
            return redirect(url_for("index"))
        flash("Login fehlgeschlagen: Benutzername oder Passwort falsch.")
    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
def logout() -> ResponseReturnValue:
    """Meldet ab und leert die Sitzung."""
    session.clear()
    return redirect(url_for("auth.login"))


@functools.cache
def _platzhalter_hash() -> str:
    return generate_password_hash(secrets.token_urlsafe())
