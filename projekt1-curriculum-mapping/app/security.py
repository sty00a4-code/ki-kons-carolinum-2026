"""Tokens, CSRF-Schutz und Login-Pflicht.

Auswertungen werden über ein zufälliges Token adressiert, nicht über ihre ID.
"""

import functools
import secrets

from flask import redirect, session, url_for


def new_token(nbytes=12):
    return secrets.token_urlsafe(nbytes)


def csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    return session["_csrf_token"]


def check_csrf(token):
    erwartet = session.get("_csrf_token")
    return bool(erwartet) and bool(token) and secrets.compare_digest(erwartet, token)


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped
