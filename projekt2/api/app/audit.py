"""Änderungsprotokoll (Tabelle audit_log).

record() schreibt NUR in die laufende Transaktion und committet nicht. Der
Endpunkt committet danach ohnehin, so landen Änderung und Protokolleintrag
atomar zusammen oder gar nicht.
"""

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def _dump(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(dict(value), default=str, ensure_ascii=False)


def record(
    db: Session,
    user,
    action: str,
    entity: str,
    entity_id: Any,
    before: Any = None,
    after: Any = None,
    reason: str | None = None,
) -> None:
    """action: create | update | delete. before/after: Mapping oder None."""
    db.execute(
        text(
            """
            insert into audit_log
                (user_id, username, role, action, entity, entity_id,
                 before_json, after_json, reason)
            values
                (:user_id, :username, :role, :action, :entity, :entity_id,
                 :before_json, :after_json, :reason)
            """
        ),
        {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "action": action,
            "entity": entity,
            "entity_id": None if entity_id is None else str(entity_id),
            "before_json": _dump(before),
            "after_json": _dump(after),
            "reason": reason,
        },
    )
