"""Kommandozeile für Betrieb und Einrichtung.

    python -m app.cli migrate                      ausstehende Migrationen anwenden
    python -m app.cli status                       Migrationsstand und Benutzerzahl
    python -m app.cli create-user NAME ROLE [--student-id N] [--password-stdin]
    python -m app.cli list-users

Das Passwort wird abgefragt (nie als Argument, sonst steht es in der
Shell-Historie). Für Skripte: --password-stdin liest es aus der Standardeingabe.
Den ersten Admin legt man hiermit an, bevor man PROJEKT2_JWT_SECRET setzt.
"""

import argparse
import getpass
import sys

from sqlalchemy.exc import IntegrityError

from . import database
from .migrations import MIGRATIONS, current_version, migrate, pending_migrations
from .repositories import users as users_repo
from .security import ROLES


def _cmd_migrate(_args) -> int:
    applied = migrate(database.engine)
    if not applied:
        print("Datenbank ist aktuell.")
    for m in applied:
        print(f"Migration {m.version} angewendet: {m.name}")
    return 0


def _cmd_status(_args) -> int:
    print(f"Datenbank: {database.DB_PATH}")
    print(f"Stand: Migration {current_version(database.engine)} von {MIGRATIONS[-1].version}")
    for m in pending_migrations(database.engine):
        print(f"  ausstehend: {m.version} {m.name}")
    return 0


def _read_password(from_stdin: bool) -> str:
    if from_stdin:
        return sys.stdin.readline().rstrip("\n")
    first = getpass.getpass("Passwort (mind. 10 Zeichen): ")
    if first != getpass.getpass("Passwort wiederholen: "):
        raise SystemExit("Passwörter stimmen nicht überein.")
    return first


def _cmd_create_user(args) -> int:
    migrate(database.engine)  # sicherstellen, dass die users-Tabelle existiert
    if args.role == "student" and args.student_id is None:
        raise SystemExit("Rolle student braucht --student-id.")
    if args.role != "student" and args.student_id is not None:
        raise SystemExit("--student-id gibt es nur für die Rolle student.")
    password = _read_password(args.password_stdin)
    if len(password) < 10:
        raise SystemExit("Das Passwort ist zu kurz (mindestens 10 Zeichen).")
    with database.SessionLocal() as db:
        if args.student_id is not None and not users_repo.student_exists(
            db, args.student_id
        ):
            raise SystemExit(f"Unbekannte student_id: {args.student_id}")
        try:
            user_id = users_repo.create_user(
                db, args.username, password, args.role, args.student_id
            )
            db.commit()
        except IntegrityError:
            raise SystemExit(f"Benutzername schon vergeben: {args.username}") from None
    print(f"Benutzer {args.username} ({args.role}) angelegt, id {user_id}.")
    return 0


def _cmd_list_users(_args) -> int:
    with database.SessionLocal() as db:
        for row in users_repo.list_users(db, limit=1000, offset=0):
            state = "aktiv" if row["active"] else "gesperrt"
            link = f" student_id={row['student_id']}" if row["student_id"] is not None else ""
            print(f"{row['id']:>4}  {row['username']:<24} {row['role']:<8} {state}{link}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("migrate").set_defaults(func=_cmd_migrate)
    sub.add_parser("status").set_defaults(func=_cmd_status)
    sub.add_parser("list-users").set_defaults(func=_cmd_list_users)
    create = sub.add_parser("create-user")
    create.add_argument("username")
    create.add_argument("role", choices=ROLES)
    create.add_argument("--student-id", type=int)
    create.add_argument("--password-stdin", action="store_true")
    create.set_defaults(func=_cmd_create_user)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
