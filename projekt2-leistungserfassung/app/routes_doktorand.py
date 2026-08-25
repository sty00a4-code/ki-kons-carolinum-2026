"""Routen für Doktoranden (Prüfer) – der EINZIGE, der Daten einträgt.

Der Doktorand wählt eine/n Studierende/n und trägt für sie/ihn Leistungen ein.
Eingetragene Leistungen zählen sofort (status='approved', signiert vom Prüfer).
Klarnamen sind hier bewusst sichtbar – der Doktorand kennt alle Studierenden.
"""

import time
from datetime import datetime

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from .catalog import CATALOG, SEMESTERS, TOTAL_TARGET, find_item, validate
from .db import get_db
from .security import new_token, role_required

bp = Blueprint("doktorand", __name__)


@bp.route("/bot/betreuer-frage", methods=["POST"])
@role_required("doktorand", "admin")
def bot_betreuer_frage():
    """Lehrenden-Bot: Jahrgangs-Übersicht und Zuteilungs-Empfehlungen (KI)."""
    frage = (request.form.get("frage") or "").strip()[:400]
    if not frage:
        return jsonify(antwort="Bitte stelle eine Frage.", quelle="regelwerk")
    now = time.time()
    if now - session.get("_bot_last", 0) < 5:
        return jsonify(
            antwort="Einen Moment bitte – die letzte Frage wird noch beantwortet.",
            quelle="regelwerk",
        )
    session["_bot_last"] = now

    from .bot_ai import ask_lehrende
    from .matching import kohorten_context

    ctx = kohorten_context(get_db())
    antwort, quelle = ask_lehrende(
        frage, ctx, allow_ai=not current_app.config.get("TESTING")
    )
    return jsonify(antwort=antwort, quelle=quelle)


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _student_or_404(pseudonym):
    s = (
        get_db()
        .execute("select * from students where pseudonym = ?", (pseudonym,))
        .fetchone()
    )
    if s is None:
        abort(404)
    return s


@bp.route("/studierende")
@role_required("doktorand", "admin")
def liste():
    db = get_db()
    students = db.execute(
        "select * from students order by real_name, pseudonym"
    ).fetchall()
    overview = []
    for s in students:
        rows = db.execute(
            "select points, count from performances where student_id = ? and status='approved'",
            (s["id"],),
        ).fetchall()
        approved = sum(r["points"] * r["count"] for r in rows)
        pct = round(min(100, approved / TOTAL_TARGET * 100), 1) if TOTAL_TARGET else 0
        overview.append(
            {"s": s, "approved": approved, "target": TOTAL_TARGET, "pct": pct}
        )
    return render_template("doktorand_liste.html", overview=overview)


@bp.route("/student/<pseudonym>")
@role_required("doktorand", "admin")
def student(pseudonym):
    s = _student_or_404(pseudonym)
    db = get_db()
    rows = db.execute(
        "select * from performances where student_id = ? order by performed_on desc, id desc",
        (s["id"],),
    ).fetchall()
    from .matching import recommend_cases_for_student

    empfehlungen = recommend_cases_for_student(db, s["id"])
    open_fall_refs = [
        r["case_ref"]
        for r in db.execute(
            "select case_ref from patient_cases where status != 'abgeschlossen' order by case_ref"
        ).fetchall()
    ]
    return render_template(
        "doktorand_student.html",
        s=s,
        rows=rows,
        catalog=CATALOG,
        semesters=SEMESTERS,
        empfehlungen=empfehlungen,
        open_fall_refs=open_fall_refs,
    )


@bp.route("/student/<pseudonym>/eintragen", methods=["POST"])
@role_required("doktorand", "admin")
def add_entry(pseudonym):
    s = _student_or_404(pseudonym)
    db = get_db()
    item = find_item(request.form.get("item_code", ""))
    semester = request.form.get("semester", "")
    try:
        count = int(request.form.get("count", "0"))
        points = float(request.form.get("points", "0").replace(",", "."))
    except ValueError:
        flash("Anzahl und Punkte müssen Zahlen sein.")
        return redirect(url_for("doktorand.student", pseudonym=pseudonym))

    if semester not in SEMESTERS:
        flash("Bitte ein gültiges Semester wählen.")
        return redirect(url_for("doktorand.student", pseudonym=pseudonym))
    err = validate(item, count, points)
    if err:
        flash(err)
        return redirect(url_for("doktorand.student", pseudonym=pseudonym))

    now = _now()
    db.execute(
        "insert into performances (public_token, student_id, semester, category, "
        "item_code, item_name, count, points, patient_ref, performed_on, difficulty, "
        "time_minutes, note, status, created_at, submitted_at, reviewed_by, reviewed_at, "
        "review_comment) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            new_token(),
            s["id"],
            semester,
            item["category"],
            item["code"],
            item["name"],
            count,
            points,
            request.form.get("patient_ref", "").strip() or None,
            request.form.get("performed_on", "").strip() or None,
            request.form.get("difficulty") or None,
            request.form.get("time_minutes") or None,
            request.form.get("note", "").strip() or None,
            "approved",
            now,
            now,
            session["user_id"],
            now,
            "Vom Prüfer eingetragen.",
        ),
    )
    db.commit()
    flash(f"Leistung für {s['real_name'] or s['pseudonym']} eingetragen.")
    return redirect(url_for("doktorand.student", pseudonym=pseudonym))


@bp.route("/eintrag/<token>/loeschen", methods=["POST"])
@role_required("doktorand", "admin")
def delete_entry(token):
    db = get_db()
    perf = db.execute(
        "select p.*, s.pseudonym from performances p "
        "join students s on p.student_id = s.id where p.public_token = ?",
        (token,),
    ).fetchone()
    if perf is None:
        abort(404)
    db.execute("delete from performances where id = ?", (perf["id"],))
    db.commit()
    flash("Eintrag gelöscht.")
    return redirect(url_for("doktorand.student", pseudonym=perf["pseudonym"]))
