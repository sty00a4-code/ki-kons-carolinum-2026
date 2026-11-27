"""Datenzugriff auf die Tabelle users (Router -> Repository)."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..passwords import hash_password

_COLUMNS = "id, username, role, student_id, active, created_at, last_login_at"


def get_by_id(db: Session, user_id: int):
    return (
        db.execute(
            text(f"select {_COLUMNS} from users where id = :id"), {"id": user_id}
        )
        .mappings()
        .first()
    )


def get_by_username(db: Session, username: str):
    """Inklusive password_hash, nur für den Login gedacht."""
    return (
        db.execute(
            text(f"select {_COLUMNS}, password_hash from users where username = :u"),
            {"u": username},
        )
        .mappings()
        .first()
    )


def list_users(db: Session, limit: int, offset: int):
    return (
        db.execute(
            text(f"select {_COLUMNS} from users order by id limit :l offset :o"),
            {"l": limit, "o": offset},
        )
        .mappings()
        .all()
    )


def count_users(db: Session) -> int:
    return db.execute(text("select count(*) from users")).scalar()


def create_user(
    db: Session, username: str, password: str, role: str, student_id: int | None
) -> int:
    """Legt den Benutzer an (kein Commit) und gibt die ID zurück."""
    result = db.execute(
        text(
            """
            insert into users (username, password_hash, role, student_id)
            values (:username, :password_hash, :role, :student_id)
            """
        ),
        {
            "username": username,
            "password_hash": hash_password(password),
            "role": role,
            "student_id": student_id,
        },
    )
    return result.lastrowid


def update_user(db: Session, user_id: int, changes: dict) -> None:
    """changes: Teilmenge aus role, student_id, active, password (kein Commit)."""
    values = dict(changes)
    if "password" in values:
        values["password_hash"] = hash_password(values.pop("password"))
    if "active" in values:
        values["active"] = int(bool(values["active"]))
    if not values:
        return
    set_clause = ", ".join(f"{column} = :{column}" for column in values)
    db.execute(
        text(f"update users set {set_clause} where id = :user_id"),
        {**values, "user_id": user_id},
    )


def touch_login(db: Session, user_id: int) -> None:
    db.execute(
        text("update users set last_login_at = current_timestamp where id = :id"),
        {"id": user_id},
    )


def student_exists(db: Session, student_id: int) -> bool:
    return (
        db.execute(
            text("select 1 from students where id = :id"), {"id": student_id}
        ).first()
        is not None
    )
