"""Sicherheits-Bausteine: Tokens, CSRF, Rollen-/Login-Schutz.

Kernprinzip gegen "Zugriff durch Ändern einer Zahl" (IDOR):
- IDs werden nie in URLs verwendet, stattdessen zufällige Tokens (new_token).
- Jede Route prüft serverseitig Rolle UND Eigentümerschaft.
"""

import functools
import secrets

from flask import abort, redirect, session, url_for


def new_token(nbytes: int = 12) -> str:
    """Zufälliger, nicht erratbarer/nicht hochzählbarer Token."""
    return secrets.token_urlsafe(nbytes)


def csrf_token() -> str:
    """CSRF-Token pro Session (für Formulare)."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    return session["_csrf_token"]


def check_csrf(form_token: str) -> bool:
    real = session.get("_csrf_token")
    return bool(real) and bool(form_token) and secrets.compare_digest(real, form_token)


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def role_required(*roles):
    def decorator(view):
        @functools.wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("auth.login"))
            if session.get("role") not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator
