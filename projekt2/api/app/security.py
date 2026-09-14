"""Minimale Absicherung der Schreib-Endpunkte über einen API-Schlüssel.

Ist die Umgebungsvariable PROJEKT2_API_KEY gesetzt, verlangen Schreib-Endpunkte
den Header X-API-Key mit genau diesem Wert. Ohne die Variable bleibt alles offen
(lokale Entwicklung). Das ist ein Zwischenschritt, bis echte Rollen kommen
(JWT oder Uni-SSO, siehe README).
"""

import hmac
import os

from fastapi import Header, HTTPException


def require_write_key(x_api_key: str | None = Header(default=None)):
    """FastAPI-Dependency: prüft den Header X-API-Key gegen PROJEKT2_API_KEY."""
    expected = os.environ.get("PROJEKT2_API_KEY")
    if not expected:
        return
    if x_api_key is None or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=401, detail="Fehlender oder ungültiger X-API-Key"
        )
