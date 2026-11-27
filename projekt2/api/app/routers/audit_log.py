"""Lesezugriff auf das Änderungsprotokoll (nur Admin)."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..pagination import Page, fetch_page, page_params
from ..schemas import AuditEntry
from ..security import admin_only

router = APIRouter(
    prefix="/audit-log", tags=["audit"], dependencies=[Depends(admin_only)]
)


def _parse(raw: str | None):
    return json.loads(raw) if raw else None


@router.get("", response_model=list[AuditEntry])
def list_audit_log(
    response: Response,
    entity: Annotated[str | None, Query(max_length=50)] = None,
    entity_id: Annotated[str | None, Query(max_length=100)] = None,
    action: Annotated[str | None, Query(pattern="^(create|update|delete)$")] = None,
    username: Annotated[str | None, Query(max_length=100)] = None,
    page: Page = Depends(page_params),
    db: Session = Depends(get_db),
):
    """Wer hat wann was geändert, mit Zustand vorher/nachher. Neueste zuerst.
    Beispiel: ?entity=treatment_case&entity_id=7 zeigt die Geschichte einer
    Behandlung samt späterer Korrekturen und ihrer Löschung."""
    rows = fetch_page(
        db,
        response,
        """
        select id, ts, user_id, username, role, action, entity, entity_id,
               before_json, after_json, reason
        from audit_log
        where (:entity is null or entity = :entity)
          and (:entity_id is null or entity_id = :entity_id)
          and (:action is null or action = :action)
          and (:username is null or username = :username)
        order by id desc
        """,
        {
            "entity": entity,
            "entity_id": entity_id,
            "action": action,
            "username": username,
        },
        page,
    )
    return [
        AuditEntry(
            id=r["id"],
            ts=r["ts"],
            user_id=r["user_id"],
            username=r["username"],
            role=r["role"],
            action=r["action"],
            entity=r["entity"],
            entity_id=r["entity_id"],
            before=_parse(r["before_json"]),
            after=_parse(r["after_json"]),
            reason=r["reason"],
        )
        for r in rows
    ]
