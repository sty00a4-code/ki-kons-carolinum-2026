"""Zentrale Konfiguration über Umgebungsvariablen.

Alle Werte werden bei jedem Aufruf frisch gelesen (nicht beim Import), damit
Tests sie per monkeypatch ändern können und ein Neustart reicht, um sie zu
wechseln.

PROJEKT2_ENV             development (Standard) | production
PROJEKT2_JWT_SECRET      Signierschlüssel für Zugriffstokens, mind. 32 Zeichen
PROJEKT2_TOKEN_MINUTES   Gültigkeit eines Zugriffstokens, Standard 60
PROJEKT2_API_KEY         optionaler Dienst-Schlüssel (X-API-Key), gilt als Admin
PROJEKT2_CORS_ORIGINS    kommagetrennte Liste erlaubter UI-Origins
PROJEKT2_AUTO_MIGRATE    1/0, Standard: an in development, aus in production
PROJEKT2_DOCS            1/0, Swagger-UI, Standard: an in development, aus in production
PROJEKT2_DB              Pfad der SQLite-Datei (siehe database.py)
"""

import os

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
MIN_SECRET_LENGTH = 32


def _get(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    return value if value not in (None, "") else default


def _flag(name: str, default: bool) -> bool:
    value = _get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def environment() -> str:
    return (_get("PROJEKT2_ENV", "development") or "development").strip().lower()


def is_production() -> bool:
    return environment() == "production"


def jwt_secret() -> str | None:
    return _get("PROJEKT2_JWT_SECRET")


def api_key() -> str | None:
    return _get("PROJEKT2_API_KEY")


def token_ttl_minutes() -> int:
    try:
        return max(1, int(_get("PROJEKT2_TOKEN_MINUTES", "60") or "60"))
    except ValueError:
        return 60


def cors_origins() -> list[str]:
    raw = _get("PROJEKT2_CORS_ORIGINS")
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    # Ohne Angabe: in der Entwicklung offen, in Produktion gar kein CORS.
    return [] if is_production() else ["*"]


def auto_migrate() -> bool:
    return _flag("PROJEKT2_AUTO_MIGRATE", default=not is_production())


def docs_enabled() -> bool:
    return _flag("PROJEKT2_DOCS", default=not is_production())


def validate_startup_config() -> list[str]:
    """Liefert die Gründe, warum die API so NICHT starten darf (fail closed).
    In der Entwicklung ist alles erlaubt, in Produktion nicht."""
    if not is_production():
        return []
    problems = []
    secret = jwt_secret()
    if not secret:
        problems.append("PROJEKT2_JWT_SECRET ist nicht gesetzt")
    elif len(secret) < MIN_SECRET_LENGTH:
        problems.append(
            f"PROJEKT2_JWT_SECRET ist zu kurz (mindestens {MIN_SECRET_LENGTH} Zeichen)"
        )
    if "*" in cors_origins():
        problems.append("PROJEKT2_CORS_ORIGINS darf in Produktion kein * enthalten")
    return problems
