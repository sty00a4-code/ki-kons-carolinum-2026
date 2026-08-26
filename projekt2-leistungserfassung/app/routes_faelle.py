"""Routen für Patientenfälle – NUR Doktoranden/Profs tragen Fälle ein.

DATENSCHUTZ: Fälle sind ANONYM (Fall-Nr. + Behandlungsbedarf + Schwierigkeit/
Dauer/Setting). Es werden KEINE Patientendaten erfasst – das Formular sagt
das explizit. Studierende sehen Fälle nur als Empfehlung auf "Mein Stand"
(ohne zu sehen, wem sonst ein Fall zugewiesen ist).
"""

from datetime import datetime

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from .catalog import CATALOG, find_item
from .db import get_db
from .matching import best_students_for_case
from .security import new_token, role_required

bp = Blueprint("faelle", __name__)

MAX_ITEMS = 4  # Formular-Zeilen für Leistungen je Fall


def _case_or_404(token):
    case = (
        get_db()
        .execute("select * from patient_cases where public_token = ?", (token,))
        .fetchone()
    )
    if case is None:
        abort(404)
    return case


@bp.route("/faelle")
@role_required("doktorand", "admin")
def liste():
    db = get_db()
    cases = db.execute(
        "select c.*, s.real_name as assigned_name from patient_cases c "
        "left join students s on c.assigned_student_id = s.id "
        "order by case when c.status='offen' then 0 when c.status='zugewiesen' then 1 "
        "else 2 end, c.created_at desc, c.id desc"
    ).fetchall()
    rows = []
    for case in cases:
        items = db.execute(
            "select * from patient_case_items where case_id = ?", (case["id"],)
        ).fetchall()
        best = (
            best_students_for_case(db, case, limit=1)
            if case["status"] == "offen"
            else []
        )
        # Schlüssel heißt bewusst nicht "items" – kollidiert in Jinja mit dict.items
        rows.append(
            {"case": case, "leistungen": items, "best": best[0] if best else None}
        )
    students = db.execute("select * from students order by real_name").fetchall()
    return render_template(
        "faelle.html",
        rows=rows,
        catalog=CATALOG,
        students=students,
        max_items=MAX_ITEMS,
    )


@bp.route("/faelle/neu", methods=["POST"])
@role_required("doktorand", "admin")
def neu():
    db = get_db()
    case_ref = request.form.get("case_ref", "").strip()[:100]
    if not case_ref:
        flash("Bitte eine anonyme Fall-Nr. angeben (z. B. Fall-051).")
        return redirect(url_for("faelle.liste"))
    if db.execute(
        "select 1 from patient_cases where case_ref = ?", (case_ref,)
    ).fetchone():
        flash(f"Fall-Nr. „{case_ref}“ existiert schon.")
        return redirect(url_for("faelle.liste"))

    items = []
    for i in range(MAX_ITEMS):
        code = request.form.get(f"item_code_{i}", "")
        if not code:
            continue
        item = find_item(code)
        if item is None:
            flash("Unbekannte Leistung im Katalog.")
            return redirect(url_for("faelle.liste"))
        try:
            cnt = min(20, max(1, int(request.form.get(f"item_count_{i}", "1"))))
        except ValueError:
            cnt = 1
        items.append((item, cnt))
    if not items:
        flash("Bitte mindestens eine Leistung aus dem Katalog wählen.")
        return redirect(url_for("faelle.liste"))

    difficulty = request.form.get("difficulty") or None
    if difficulty is not None and difficulty not in ("1", "2", "3"):
        difficulty = None
    try:
        est = int(request.form.get("est_minutes", "") or 0)
        est = est if est > 0 else None
    except ValueError:
        est = None

    cur = db.execute(
        "insert into patient_cases (public_token, case_ref, description, difficulty, "
        "est_minutes, status, created_by, created_at) values (?,?,?,?,?,?,?,?)",
        (
            new_token(),
            case_ref,
            request.form.get("description", "").strip()[:500] or None,
            difficulty,
            est,
            "offen",
            session["user_id"],
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    case_id = cur.lastrowid
    for item, cnt in items:
        db.execute(
            "insert into patient_case_items (case_id, item_code, item_name, category, "
            "count, points) values (?,?,?,?,?,?)",
            (
                case_id,
                item["code"],
                item["name"],
                item["category"],
                cnt,
                item["points_min"] * cnt,
            ),
        )
    db.commit()
    flash(f"Fall „{case_ref}“ angelegt.")
    return redirect(url_for("faelle.liste"))


@bp.route("/faelle/<token>/status", methods=["POST"])
@role_required("doktorand", "admin")
def set_status(token):
    case = _case_or_404(token)
    db = get_db()
    status = request.form.get("status", "")
    if status not in ("offen", "zugewiesen", "abgeschlossen"):
        abort(400)
    # Zuweisung bleibt beim Abschließen erhalten (Nachvollziehbarkeit);
    # nur "offen" löscht sie explizit.
    assigned = case["assigned_student_id"]
    if status == "offen":
        assigned = None
    elif status == "zugewiesen":
        pseudonym = request.form.get("assigned_pseudonym", "")
        s = (
            db.execute(
                "select id from students where pseudonym = ?", (pseudonym,)
            ).fetchone()
            if pseudonym
            else None
        )
        if s is None:
            flash("Für „zugewiesen“ bitte eine/n Studierende/n auswählen.")
            return redirect(url_for("faelle.liste"))
        assigned = s["id"]
    db.execute(
        "update patient_cases set status = ?, assigned_student_id = ? where id = ?",
        (status, assigned, case["id"]),
    )
    db.commit()
    flash(f"Fall „{case['case_ref']}“ → {status}.")
    return redirect(url_for("faelle.liste"))


@bp.route("/faelle/<token>/loeschen", methods=["POST"])
@role_required("doktorand", "admin")
def loeschen(token):
    case = _case_or_404(token)
    db = get_db()
    db.execute("delete from patient_case_items where case_id = ?", (case["id"],))
    db.execute("delete from patient_cases where id = ?", (case["id"],))
    db.commit()
    flash(f"Fall „{case['case_ref']}“ gelöscht.")
    return redirect(url_for("faelle.liste"))
