"""Einheitliches Fehlerformat (angelehnt an RFC 7807 Problem Details).

Jede Fehlerantwort, egal woher (eigene HTTPException, Validierung, unbekannter
Pfad, unerwarteter Fehler), hat dieselbe Form:

    {"type": "validation_error", "title": "Unprocessable Entity", "status": 422,
     "detail": "student_id: Field required", "request_id": "...",
     "errors": [{"location": "body", "field": "student_id", "message": "..."}]}

`detail` bleibt ein String, wie bisher bei eigenen Fehlern. `errors` gibt es
nur bei Validierungsfehlern der Eingabe.
"""

import logging
from http import HTTPStatus

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("projekt2.errors")

_TYPES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_error",
    429: "too_many_requests",
    503: "unavailable",
}


def problem_response(
    request: Request,
    status: int,
    detail: str,
    errors: list[dict] | None = None,
    headers: dict | None = None,
) -> JSONResponse:
    try:
        title = HTTPStatus(status).phrase
    except ValueError:
        title = "Error"
    body = {
        "type": _TYPES.get(status, "internal_error" if status >= 500 else "error"),
        "title": title,
        "status": status,
        "detail": detail,
        "request_id": getattr(request.state, "request_id", None),
    }
    if errors:
        body["errors"] = errors
    return JSONResponse(
        body,
        status_code=status,
        headers=headers,
        media_type="application/problem+json",
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return problem_response(request, exc.status_code, detail, headers=exc.headers)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        loc = [str(part) for part in error.get("loc", ())]
        errors.append(
            {
                "location": loc[0] if loc else "",
                "field": ".".join(loc[1:]),
                "message": error.get("msg", ""),
            }
        )
    summary = "; ".join(
        f"{e['field']}: {e['message']}" if e["field"] else e["message"] for e in errors
    )
    return problem_response(
        request, 422, summary or "Eingabe ungültig", errors=errors
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unbehandelter Fehler bei %s %s", request.method, request.url.path)
    return problem_response(request, 500, "Interner Serverfehler")
