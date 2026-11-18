"""Legt die Datenbank und einen Login an.

    python -m scripts.init_db                  Testlogin doktorand1 mit Passwort doktorand1
    python -m scripts.init_db NAME [admin]     Login mit abgefragtem Passwort

Ein bestehender Login erhält das neue Passwort, vorhandene Abgleiche bleiben
erhalten.
"""

from __future__ import annotations

import argparse
import getpass
import sys
from collections.abc import Callable, Sequence
from contextlib import closing
from pathlib import Path

from werkzeug.security import generate_password_hash

from app import db

MIN_PASSWORT = 10
TESTLOGIN = "doktorand1"
ROLLEN = ("doktorand", "admin")

_LOGIN_SPEICHERN = """
insert into users (username, password_hash, role) values (:name, :hash, :rolle)
on conflict (username) do update
set password_hash = excluded.password_hash, role = excluded.role
"""

Eingabe = Callable[[str], str]


class PasswortFehler(ValueError):
    """Das Passwort ist zu kurz oder die Wiederholung weicht ab."""


def passwort_abfragen(name: str, eingabe: Eingabe = getpass.getpass) -> str:
    """Fragt das Passwort zweimal verdeckt ab."""
    passwort = eingabe(f"Passwort für {name}: ")
    if len(passwort) < MIN_PASSWORT:
        raise PasswortFehler(f"Das Passwort muss mindestens {MIN_PASSWORT} Zeichen haben.")
    if eingabe("Noch einmal: ") != passwort:
        raise PasswortFehler("Die Passwörter stimmen nicht überein.")
    return passwort


def main(argv: Sequence[str] | None = None, eingabe: Eingabe = getpass.getpass) -> int:
    """Speichert den Login und meldet die Datenbank."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("name", nargs="?", help=f"ohne Angabe der Testlogin {TESTLOGIN}")
    parser.add_argument("rolle", nargs="?", choices=ROLLEN, default=ROLLEN[0])
    parser.add_argument("--datenbank", type=Path, help="SQLite-Datei, sonst die der App")
    args = parser.parse_args(argv)
    if args.name:
        try:
            name, passwort = args.name, passwort_abfragen(args.name, eingabe)
        except PasswortFehler as exc:
            print(exc, file=sys.stderr)
            return 1
    else:
        name = passwort = TESTLOGIN

    pfad = args.datenbank or db.STANDARD_PFAD
    with closing(db.oeffnen(pfad)) as con:
        werte = {"name": name, "hash": generate_password_hash(passwort), "rolle": args.rolle}
        con.execute(_LOGIN_SPEICHERN, werte)
        con.commit()
    print(f"Login {name} ({args.rolle}) gespeichert in {pfad}")
    if not args.name:
        print("Passwort wie Benutzername, nur für den Testbetrieb.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
