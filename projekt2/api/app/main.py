import logging
import re
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import config, database
from .database import engine
from .errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from .migrations import migrate, pending_migrations
from .repositories import jobs
from .routers import (
    analysis,
    assignments,
    audit_log,
    auth,
    categories,
    classes,
    osce,
    patients,
    semesters,
    students,
    treatment_cases,
    users,
)
from .security import get_current_user

logger = logging.getLogger("projekt2")
access_logger = logging.getLogger("projekt2.access")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Startprüfungen. In Produktion bricht die API bei unsicherer
    Konfiguration oder ausstehenden Migrationen ab (fail closed), in der
    Entwicklung wendet sie Migrationen selbst an."""
    problems = config.validate_startup_config()
    if problems:
        raise RuntimeError("Unsichere Konfiguration: " + "; ".join(problems))
    if not config.jwt_secret():
        logger.warning(
            "PROJEKT2_JWT_SECRET ist nicht gesetzt: Authentifizierung ist AUS, "
            "jede Anfrage gilt als Admin (nur Entwicklungsmodus)."
        )

    if config.auto_migrate():
        for migration in migrate(engine):
            logger.info("Migration %s angewendet: %s", migration.version, migration.name)
    else:
        pending = pending_migrations(engine)
        if pending:
            raise RuntimeError(
                "Ausstehende Datenbank-Migrationen "
                f"({', '.join(str(m.version) for m in pending)}): "
                "erst `python -m app.cli migrate` ausführen."
            )

    with database.SessionLocal() as db:
        orphans = jobs.fail_orphans(db)
        db.commit()
    if orphans:
        logger.warning("%s unfertige Analyse-Jobs als fehlgeschlagen markiert", orphans)
    yield


app = FastAPI(
    title="Leistungsübersicht API",
    description=(
        "Backend für die klinische Kompetenz- und Lernverlaufsanalyse. "
        "Aktuelle Version unter /api/v1; die unversionierten Pfade sind "
        "veraltete Aliase und verschwinden mit v2."
    ),
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs" if config.docs_enabled() else None,
    redoc_url=None,
    openapi_url="/openapi.json" if config.docs_enabled() else None,
)

# Einheitliches Fehlerformat für alle Fehlerquellen (siehe errors.py).
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# CORS: ohne PROJEKT2_CORS_ORIGINS in der Entwicklung offen, in Produktion aus.
# Kein allow_credentials: die Anmeldung läuft über den Authorization-Header,
# nicht über Cookies.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins(),
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
    expose_headers=["X-Total-Count", "X-Request-ID", "Retry-After"],
)

_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


@app.middleware("http")
async def request_context(request: Request, call_next):
    """Vergibt eine Request-ID (ein passender X-Request-ID des Clients wird
    übernommen), gibt sie im Header und in Fehlern zurück und loggt Dauer."""
    supplied = request.headers.get("X-Request-ID", "")
    request_id = supplied if _REQUEST_ID.match(supplied) else uuid.uuid4().hex
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    access_logger.info(
        "%s %s -> %s (%.0f ms) rid=%s",
        request.method,
        request.url.path,
        response.status_code,
        (time.perf_counter() - started) * 1000,
        request_id,
    )
    return response


# Alles hinter der Anmeldung. Die einzelnen Endpunkte schränken zusätzlich nach
# Rolle ein (security.require_roles); wer hier keine Rolle angibt, ist
# trotzdem authentifiziert - die Absicherung ist Standard, nicht Zusatz.
_PROTECTED = [Depends(get_current_user)]
_ROUTERS = [
    students.router,
    categories.router,
    classes.router,
    semesters.router,
    patients.router,
    assignments.router,
    treatment_cases.router,
    osce.router,
    analysis.router,
]

v1 = APIRouter(prefix="/api/v1")
v1.include_router(auth.router)  # Login ist offen, /me prüft selbst
for router in _ROUTERS:
    v1.include_router(router, dependencies=_PROTECTED)
v1.include_router(users.router, dependencies=_PROTECTED)
v1.include_router(audit_log.router, dependencies=_PROTECTED)


@v1.get("/health", tags=["health"])
def health_v1():
    return {"status": "ok"}


app.include_router(v1)

# Veraltete, unversionierte Aliase: gleiche Endpunkte wie v1, aber nicht in der
# OpenAPI-Doku. Dazu die alten Kategorie-Punkte-Routen, die es in v1 nicht mehr gibt.
for router in _ROUTERS + [categories.legacy_router]:
    app.include_router(router, dependencies=_PROTECTED, include_in_schema=False)


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}
