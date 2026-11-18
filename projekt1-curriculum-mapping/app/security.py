"""Tokens, CSRF-Schutz, Login-Pflicht und Sicherheits-Header.

Datensätze werden über ein zufälliges Token adressiert, nicht über ihre ID.
Jede POST-Anfrage braucht das CSRF-Token der Sitzung im Feld _csrf_token.
"""

from __future__ import annotations

import functools
import secrets
from collections.abc import Callable
from typing import ParamSpec

from flask import Response, abort, redirect, request, session, url_for
from flask.typing import ResponseReturnValue

P = ParamSpec("P")

CSRF_FELD = "_csrf_token"

# Skripte und Styles nur aus eigenen Dateien; die Breite der Balken setzt seiten.js.
CONTENT_SECURITY_POLICY = "; ".join(
    (
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self'",
        "img-src 'self' data:",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    )
)


def new_token(nbytes: int = 12) -> str:
    """Liefert ein zufälliges, URL-taugliches Token."""
    return secrets.token_urlsafe(nbytes)


def csrf_token() -> str:
    """Liefert das CSRF-Token der Sitzung und legt es beim ersten Aufruf an."""
    if CSRF_FELD not in session:
        session[CSRF_FELD] = secrets.token_urlsafe(32)
    token: str = session[CSRF_FELD]
    return token


def check_csrf(token: str) -> bool:
    """Vergleicht ein Token zeitkonstant mit dem CSRF-Token der Sitzung."""
    erwartet = session.get(CSRF_FELD)
    if not isinstance(erwartet, str) or not erwartet or not token:
        return False
    # Als Bytes vergleichen: compare_digest lehnt Texte mit Nicht-ASCII-Zeichen ab.
    return secrets.compare_digest(erwartet.encode(), token.encode())


def csrf_pruefen() -> None:
    """Bricht POST-Anfragen ohne gültiges CSRF-Token mit Status 400 ab."""
    if request.method == "POST" and not check_csrf(request.form.get(CSRF_FELD, "")):
        abort(
            400,
            "Das Formular ist abgelaufen (CSRF-Token fehlt oder ist ungültig). "
            "Bitte die Seite neu laden und noch einmal senden.",
        )


def kopfzeilen_setzen(antwort: Response) -> Response:
    """Ergänzt Sicherheits-Header, HTML-Seiten bekommen eine Content Security Policy."""
    antwort.headers.setdefault("X-Content-Type-Options", "nosniff")
    antwort.headers.setdefault("Referrer-Policy", "same-origin")
    antwort.headers.setdefault("X-Frame-Options", "DENY")
    if antwort.mimetype == "text/html":
        antwort.headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)
    return antwort


def login_required(view: Callable[P, ResponseReturnValue]) -> Callable[P, ResponseReturnValue]:
    """Leitet Anfragen ohne Anmeldung zur Login-Seite um."""

    @functools.wraps(view)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> ResponseReturnValue:
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped
