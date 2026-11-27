"""Gemeinsame Seitenaufteilung, Sortierung für Listen-Endpunkte.

Vertrag: ?limit= (1 bis 500, Standard 100) und ?offset= (ab 0). Die
Gesamtzahl steht im Antwort-Header X-Total-Count; der Body bleibt eine
einfache Liste, bestehende Clients laufen also unverändert weiter.
"""

from dataclasses import dataclass

from fastapi import HTTPException, Query, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

DEFAULT_LIMIT = 100
MAX_LIMIT = 500


@dataclass(frozen=True)
class Page:
    limit: int
    offset: int


def page_params(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
) -> Page:
    return Page(limit=limit, offset=offset)


def fetch_page(
    db: Session, response: Response, sql: str, params: dict, page: Page
) -> list:
    """Führt `sql` (ohne limit/offset) seitenweise aus, setzt X-Total-Count und
    gibt die Zeilen als RowMappings zurück."""
    sql = sql.strip().rstrip(";").strip()
    total = db.execute(text(f"select count(*) from ({sql}) as counted"), params).scalar()
    rows = (
        db.execute(
            text(f"{sql} limit :page_limit offset :page_offset"),
            {**params, "page_limit": page.limit, "page_offset": page.offset},
        )
        .mappings()
        .all()
    )
    response.headers["X-Total-Count"] = str(total)
    return rows


def order_clause(
    sort: str | None, order: str, allowed: dict[str, str], default: str
) -> str:
    """Baut ein `order by`-Fragment aus einer Whitelist (nie aus Nutzereingabe
    direkt). allowed: API-Name -> SQL-Ausdruck."""
    if sort is None:
        return default
    if sort not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Ungültiges sort: {sort!r} (erlaubt: {', '.join(sorted(allowed))})",
        )
    direction = "desc" if order == "desc" else "asc"
    return f"{allowed[sort]} {direction}, {default}"
