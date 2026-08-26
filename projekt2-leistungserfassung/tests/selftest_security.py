"""Sicherheits-Selbsttest (ohne externe Test-Bibliothek).

    python -m tests.selftest_security

Prüft das Rollenmodell:
- Studierende sind READ-ONLY: kein Eintragen, kein Zugriff auf fremde Daten,
  keine Auswertung (Klarnamen).
- Nur Doktoranden dürfen Leistungen eintragen.
- Der Demo-Bot bekommt nur die eigenen Daten (keine Route für fremde Daten).
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import generate_password_hash

from app import create_app
from app.db import get_db, init_db
from app.security import new_token

FAILS = []
CHECKS = 0


def check(name, cond):
    global CHECKS
    CHECKS += 1
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        FAILS.append(name)


def login(client, username, password):
    client.get("/login")
    with client.session_transaction() as s:
        token = s["_csrf_token"]
    client.post(
        "/login",
        data={"username": username, "password": password, "_csrf_token": token},
        follow_redirects=True,
    )


def form_token(client):
    client.get("/", follow_redirects=True)
    with client.session_transaction() as s:
        return s.get("_csrf_token", "")


def seed(app):
    ids = {}
    with app.app_context():
        init_db()
        db = get_db()
        db.execute(
            "insert into users (username,password_hash,role,real_name) values (?,?,?,?)",
            ("dok", generate_password_hash("p"), "doktorand", "Dr. Test"),
        )
        for name in ("a", "b"):
            cur = db.execute(
                "insert into students (pseudonym,real_name,cohort) values (?,?,?)",
                ("S-" + new_token(4), "Stud " + name, "T"),
            )
            sid = cur.lastrowid
            db.execute(
                "insert into users (username,password_hash,role,student_id) values (?,?,?,?)",
                ("stud_" + name, generate_password_hash("p"), "student", sid),
            )
            ids[name] = db.execute(
                "select pseudonym from students where id=?", (sid,)
            ).fetchone()["pseudonym"]
        db.commit()
    return ids


def perf_count(app):
    with app.app_context():
        return get_db().execute("select count(*) c from performances").fetchone()["c"]


def main():
    tmp = tempfile.mkdtemp()
    app = create_app()
    app.config.update(DATABASE=os.path.join(tmp, "test.db"), TESTING=True)
    ids = seed(app)

    # 1) Ohne Login -> Redirect
    c = app.test_client()
    r = c.get("/meine", follow_redirects=False)
    check(
        "Ohne Login kein Zugriff auf /meine",
        r.status_code in (301, 302) and "/login" in r.headers.get("Location", ""),
    )

    # Student A
    ca = app.test_client()
    login(ca, "stud_a", "p")
    check(
        "Student A sieht eigenen Stand (/meine 200)",
        ca.get("/meine").status_code == 200,
    )

    # 2) Student darf NICHT auf Doktoranden-Übersicht/Auswertung (Klarnamen)
    check(
        "Student kein Zugriff auf /studierende (403)",
        ca.get("/studierende").status_code == 403,
    )
    check(
        "Student kein Zugriff auf /auswertung (403)",
        ca.get("/auswertung").status_code == 403,
    )

    # 3) Student darf NICHT die Detailseite (auch nicht die eigene, das ist Doktoranden-Route)
    check(
        "Student kein Zugriff auf /student/<B> (403)",
        ca.get(f"/student/{ids['b']}").status_code == 403,
    )

    # 4) Student darf NICHT eintragen (Schreibrecht nur Doktorand)
    r = ca.post(
        f"/student/{ids['a']}/eintragen",
        data={
            "_csrf_token": form_token(ca),
            "semester": "IK I",
            "item_code": "pa_upt",
            "count": 1,
            "points": 2,
        },
    )
    check("Student kann NICHT eintragen (403)", r.status_code == 403)

    # 5) POST ohne CSRF -> 400
    r = ca.post(f"/student/{ids['a']}/eintragen", data={})
    check("POST ohne CSRF-Token abgelehnt (400)", r.status_code == 400)

    # 6) Doktorand darf eintragen -> Redirect, Eintrag landet in DB
    before = perf_count(app)
    cd = app.test_client()
    login(cd, "dok", "p")
    r = cd.post(
        f"/student/{ids['a']}/eintragen",
        data={
            "_csrf_token": form_token(cd),
            "semester": "IK I",
            "item_code": "pa_upt",
            "count": 1,
            "points": 2,
            "patient_ref": "Fall-X",
        },
        follow_redirects=False,
    )
    after = perf_count(app)
    check("Doktorand darf eintragen (Redirect)", r.status_code in (301, 302))
    check("Eintrag wurde gespeichert (DB +1)", after == before + 1)

    # 7) Patientenfälle: nur Doktorand darf sehen/anlegen
    check(
        "Student kein Zugriff auf /faelle (403)", ca.get("/faelle").status_code == 403
    )
    r = ca.post(
        "/faelle/neu",
        data={
            "_csrf_token": form_token(ca),
            "case_ref": "Fall-T1",
            "item_code_0": "pa_upt",
        },
    )
    check("Student kann KEINEN Fall anlegen (403)", r.status_code == 403)
    check("Doktorand sieht /faelle (200)", cd.get("/faelle").status_code == 200)
    r = cd.post(
        "/faelle/neu",
        data={
            "_csrf_token": form_token(cd),
            "case_ref": "Fall-T1",
            "item_code_0": "pa_upt",
            "item_count_0": "1",
        },
        follow_redirects=False,
    )
    with app.app_context():
        n_cases = (
            get_db().execute("select count(*) c from patient_cases").fetchone()["c"]
        )
        case_token = (
            get_db()
            .execute("select public_token from patient_cases limit 1")
            .fetchone()["public_token"]
        )
    check(
        "Doktorand kann Fall anlegen (DB +1)",
        r.status_code in (301, 302) and n_cases == 1,
    )

    # 8) Fall-Detailrouten: Student 403 trotz gültigem Token, Fantasie-Token 404
    r = ca.post(
        f"/faelle/{case_token}/status",
        data={"_csrf_token": form_token(ca), "status": "offen"},
    )
    check("Student kann Fall-Status NICHT ändern (403)", r.status_code == 403)
    r = cd.post(
        "/faelle/gibtsnicht/status",
        data={"_csrf_token": form_token(cd), "status": "offen"},
    )
    check("Unbekannter Fall-Token -> 404", r.status_code == 404)

    # 9) KI-Bot: nur Studierende, nur eigene Daten (TESTING -> regelbasierte Antwort)
    r = cd.post("/bot/frage", data={"_csrf_token": form_token(cd), "frage": "Stand?"})
    check("Doktorand hat KEINEN Bot-Zugriff (403)", r.status_code == 403)
    r = ca.post(
        "/bot/frage",
        data={"_csrf_token": form_token(ca), "frage": "Wie ist mein Stand?"},
    )
    check(
        "Student-Bot antwortet (200 + JSON)",
        r.status_code == 200 and "antwort" in r.get_json(),
    )

    # 10) Lehrenden-Bot: nur Doktorand
    r = ca.post(
        "/bot/betreuer-frage", data={"_csrf_token": form_token(ca), "frage": "Kohorte?"}
    )
    check("Student hat KEINEN Betreuer-Bot-Zugriff (403)", r.status_code == 403)
    r = cd.post(
        "/bot/betreuer-frage",
        data={"_csrf_token": form_token(cd), "frage": "Wie steht die Kohorte?"},
    )
    check(
        "Betreuer-Bot antwortet (200 + JSON)",
        r.status_code == 200 and "antwort" in r.get_json(),
    )

    print(f"\n{CHECKS} Prüfungen, {len(FAILS)} Fehler")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
