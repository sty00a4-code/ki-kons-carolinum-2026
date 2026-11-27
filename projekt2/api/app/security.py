"""Authentifizierung und Autorisierung.

Anmelden: POST /api/v1/auth/login liefert ein Bearer-Token (JWT, HS256). Jede
Anfrage trägt es als `Authorization: Bearer <token>`. Das Token enthält nur die
Benutzer-ID; Rolle und Aktiv-Status werden bei jeder Anfrage aus der Datenbank
gelesen, eine Sperrung oder Rollenänderung wirkt also sofort.

Rollen: student (nur eigene Daten), teacher (lesen, Behandlungen erfassen),
admin (Katalog, Planung, Benutzer).

Betriebsarten (siehe config.py):
- PROJEKT2_JWT_SECRET gesetzt: JWT-Pflicht für alle Endpunkte außer Login und /health.
- Nicht gesetzt, development: Entwicklungsmodus, jede Anfrage gilt als Admin.
  Ist zusätzlich PROJEKT2_API_KEY gesetzt, verlangen schreibende Methoden den
  Schlüssel (X-API-Key), Lesen bleibt offen (bisheriges Verhalten).
- Nicht gesetzt, production: Start wird abgelehnt (main.py), und zur Sicherheit
  antwortet get_current_user hier ebenfalls mit 401 (fail closed).

Der X-API-Key gilt, wenn konfiguriert, in jeder Betriebsart als Dienst-Admin.
"""

import hmac
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from . import config
from .database import get_db

ROLES = ("student", "teacher", "admin")
_bearer = HTTPBearer(auto_error=False)
_ALGORITHM = "HS256"


@dataclass(frozen=True)
class User:
    id: int
    username: str
    role: str
    student_id: int | None = None
    # Wie die Anfrage authentifiziert wurde: jwt | api-key | dev
    auth: str = "jwt"


DEV_USER = User(id=0, username="dev", role="admin", auth="dev")
SERVICE_USER = User(id=0, username="api-key", role="admin", auth="api-key")


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=401, detail=detail, headers={"WWW-Authenticate": "Bearer"}
    )


def create_access_token(user_id: int, secret: str, minutes: int) -> tuple[str, int]:
    """Liefert (Token, Gültigkeit in Sekunden)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, secret, algorithm=_ALGORITHM), minutes * 60


def decode_access_token(token: str, secret: str) -> int:
    """Gibt die Benutzer-ID zurück oder wirft 401."""
    try:
        payload = jwt.decode(
            token, secret, algorithms=[_ALGORITHM], options={"require": ["exp", "sub"]}
        )
        return int(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError):
        raise _unauthorized("Ungültiges oder abgelaufenes Token") from None


def _key_matches(candidate: str | None) -> bool:
    expected = config.api_key()
    if not expected or candidate is None:
        return False
    return hmac.compare_digest(candidate.encode(), expected.encode())


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if _key_matches(x_api_key):
        return SERVICE_USER

    secret = config.jwt_secret()
    if secret:
        if credentials is None:
            raise _unauthorized("Anmeldung erforderlich")
        # Import hier, um einen Importzyklus zu vermeiden (repositories -> security).
        from .repositories import users as users_repo

        user_id = decode_access_token(credentials.credentials, secret)
        row = users_repo.get_by_id(db, user_id)
        if row is None or not row["active"]:
            raise _unauthorized("Benutzer unbekannt oder gesperrt")
        return User(
            id=row["id"],
            username=row["username"],
            role=row["role"],
            student_id=row["student_id"],
        )

    if config.is_production():
        # Fail closed: ohne Auth-Konfiguration nie "alles offen".
        raise _unauthorized("Authentifizierung ist nicht konfiguriert")

    if config.api_key() and request.method not in config.SAFE_METHODS:
        raise _unauthorized("Fehlender oder ungültiger X-API-Key")
    return DEV_USER


def require_roles(*allowed: str):
    """Dependency-Fabrik: `Depends(require_roles("teacher", "admin"))`.
    Liefert den User, damit der Endpunkt ihn z.B. fürs Audit-Log nutzen kann."""
    unknown = set(allowed) - set(ROLES)
    if unknown:
        raise ValueError(f"Unbekannte Rollen: {unknown}")

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Rolle '{user.role}' darf das nicht (erlaubt: {', '.join(allowed)})",
            )
        return user

    return dependency


# Häufige Kombinationen, damit die Router lesbar bleiben.
any_user = get_current_user
staff = require_roles("teacher", "admin")
admin_only = require_roles("admin")


def ensure_student_access(user: User, student_id: int) -> None:
    """Studierende dürfen nur ihre eigenen Daten sehen; Lehrende und Admins alles."""
    if user.role == "student" and user.student_id != student_id:
        raise HTTPException(status_code=403, detail="Kein Zugriff auf fremde Daten")


def scoped_student_id(user: User, requested: int | None) -> int | None:
    """Für Listen-Filter: Studierende werden auf sich selbst festgelegt, ein
    abweichender Wunsch ist 403. Sonst gilt der gewünschte Filter unverändert."""
    if user.role != "student":
        return requested
    if user.student_id is None:
        raise HTTPException(status_code=403, detail="Konto ist keinem Studierenden zugeordnet")
    if requested is not None and requested != user.student_id:
        raise HTTPException(status_code=403, detail="Kein Zugriff auf fremde Daten")
    return user.student_id
