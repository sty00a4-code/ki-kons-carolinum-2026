"""Benutzerverwaltung (nur Admin). Passwörter werden nie zurückgegeben."""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import audit
from ..database import get_db
from ..pagination import Page, page_params
from ..repositories import users as users_repo
from ..schemas import UserCreate, UserOut, UserUpdate
from ..security import User, admin_only

router = APIRouter(prefix="/users", tags=["users"])


def _out(row) -> UserOut:
    return UserOut.model_validate({**row, "active": bool(row["active"])})


def _snapshot(row) -> dict:
    return {k: row[k] for k in ("username", "role", "student_id", "active")}


@router.get("", response_model=list[UserOut])
def list_users(
    response: Response,
    page: Page = Depends(page_params),
    _: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    response.headers["X-Total-Count"] = str(users_repo.count_users(db))
    return [_out(r) for r in users_repo.list_users(db, page.limit, page.offset)]


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    payload: UserCreate,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    """Legt einen Benutzer an. Rolle student braucht eine student_id (422 bei
    unbekannter), Benutzername und student_id sind eindeutig (409)."""
    if payload.student_id is not None and not users_repo.student_exists(
        db, payload.student_id
    ):
        raise HTTPException(
            status_code=422, detail=f"Unbekannte student_id: {payload.student_id}"
        )
    if users_repo.get_by_username(db, payload.username) is not None:
        raise HTTPException(
            status_code=409, detail=f"Benutzername schon vergeben: {payload.username}"
        )
    if payload.student_id is not None and users_repo.student_account_id(
        db, payload.student_id
    ):
        raise HTTPException(
            status_code=409,
            detail=f"student_id {payload.student_id} hat schon ein Konto",
        )
    try:
        new_id = users_repo.create_user(
            db, payload.username, payload.password, payload.role, payload.student_id
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail=f"Benutzername schon vergeben: {payload.username}"
        ) from None
    created = users_repo.get_by_id(db, new_id)
    audit.record(db, user, "create", "user", new_id, after=_snapshot(created))
    db.commit()
    return _out(created)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    """Rolle ändern, sperren/entsperren, Passwort zurücksetzen. Nur gesendete
    Felder ändern sich. Der eigene Zugang lässt sich nicht sperren oder
    herabstufen (409), damit sich niemand aussperrt."""
    current = users_repo.get_by_id(db, user_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    changes = payload.model_dump(exclude_unset=True)
    if "role" in changes and changes["role"] is None:
        raise HTTPException(status_code=422, detail="role darf nicht null sein")
    if "active" in changes and changes["active"] is None:
        raise HTTPException(status_code=422, detail="active darf nicht null sein")
    if changes.get("password") is None:
        changes.pop("password", None)

    role = changes.get("role", current["role"])
    student_id = changes.get("student_id", current["student_id"])
    if role == "student" and student_id is None:
        raise HTTPException(status_code=422, detail="student_id ist für die Rolle student Pflicht")
    if role != "student":
        if "student_id" in changes and changes["student_id"] is not None:
            raise HTTPException(
                status_code=422, detail="student_id ist nur für die Rolle student erlaubt"
            )
        # Beim Wechsel weg von student die Verknüpfung mit lösen.
        if current["student_id"] is not None:
            changes["student_id"] = None
    if student_id is not None and not users_repo.student_exists(db, student_id):
        raise HTTPException(status_code=422, detail=f"Unbekannte student_id: {student_id}")
    if student_id is not None:
        owner = users_repo.student_account_id(db, student_id)
        if owner is not None and owner != user_id:
            raise HTTPException(
                status_code=409, detail=f"student_id {student_id} hat schon ein Konto"
            )

    if user_id == user.id and (
        changes.get("active") is False or role != "admin"
    ):
        raise HTTPException(
            status_code=409,
            detail="Der eigene Zugang kann nicht gesperrt oder herabgestuft werden",
        )

    users_repo.update_user(db, user_id, changes)
    updated = users_repo.get_by_id(db, user_id)
    audit.record(
        db,
        user,
        "update",
        "user",
        user_id,
        before=_snapshot(current),
        # Ein Passwort-Reset taucht nur als Hinweis auf, nie als Wert.
        after={**_snapshot(updated), **({"password": "(zurückgesetzt)"} if "password" in changes else {})},
    )
    db.commit()
    return _out(updated)
