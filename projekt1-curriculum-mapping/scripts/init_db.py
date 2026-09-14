"""Legt die Datenbank und einen Login an.

    python -m scripts.init_db                  Testlogin doktorand1 mit Passwort doktorand1
    python -m scripts.init_db NAME [admin]     Login mit abgefragtem Passwort

Ein bestehender Login erhält das neue Passwort, vorhandene Auswertungen
bleiben erhalten.
"""

import argparse
import getpass
import sys

from werkzeug.security import generate_password_hash

from app import create_app
from app.db import get_db

MIN_PASSWORT = 10
TESTLOGIN = "doktorand1"


def passwort_abfragen(name):
    passwort = getpass.getpass(f"Passwort für {name}: ")
    if len(passwort) < MIN_PASSWORT:
        sys.exit(f"Das Passwort muss mindestens {MIN_PASSWORT} Zeichen haben.")
    if getpass.getpass("Noch einmal: ") != passwort:
        sys.exit("Die Passwörter stimmen nicht überein.")
    return passwort


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("name", nargs="?", help=f"ohne Angabe der Testlogin {TESTLOGIN}")
    parser.add_argument("rolle", nargs="?", choices=["doktorand", "admin"], default="doktorand")
    args = parser.parse_args()
    if args.name:
        name, passwort = args.name, passwort_abfragen(args.name)
    else:
        name = passwort = TESTLOGIN

    app = create_app()
    with app.app_context():
        con = get_db()
        con.execute(
            "insert into users (username, password_hash, role) values (?, ?, ?) "
            "on conflict (username) do update set password_hash = excluded.password_hash, "
            "role = excluded.role",
            (name, generate_password_hash(passwort), args.rolle),
        )
        con.commit()
        print(f"Login {name} ({args.rolle}) gespeichert in {app.config['DATABASE']}")
        if not args.name:
            print("Passwort wie Benutzername, nur für den Testbetrieb.")


if __name__ == "__main__":
    main()
