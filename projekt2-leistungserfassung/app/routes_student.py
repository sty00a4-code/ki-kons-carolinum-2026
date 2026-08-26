"""Routen für Studierende – NUR LESEN (plus KI-Bot-Frage über eigene Daten).

Studierende können sich anmelden und ihren eigenen Stand ansehen. Sie können
NICHTS eintragen, ändern oder löschen – das macht ausschließlich der Doktorand.
Die eigene Identität kommt immer aus der Session (session['student_id']).
Der Bot-Endpoint ist die einzige POST-Route für Studierende und ändert keine
Daten – er beantwortet nur Fragen über die EIGENEN Daten.
"""

import time

from flask import Blueprint, current_app, jsonify, render_template, request, session

from . import student_stats
from .catalog import CATALOG, CATEGORY_TARGET
from .db import get_db
from .security import role_required

bp = Blueprint("student", __name__)

BOT_MIN_INTERVAL_S = 5  # einfache Bremse gegen Frage-Spam
BOT_MAX_QUESTION_LEN = 400


@bp.route("/bot/frage", methods=["POST"])
@role_required("student")
def bot_frage():
    """KI-Assistent: beantwortet eine Freitext-Frage über die EIGENEN Daten."""
    frage = (request.form.get("frage") or "").strip()[:BOT_MAX_QUESTION_LEN]
    if not frage:
        return jsonify(antwort="Bitte stelle eine Frage.", quelle="regelwerk")
    now = time.time()
    last = session.get("_bot_last", 0)
    if now - last < BOT_MIN_INTERVAL_S:
        return jsonify(
            antwort="Einen Moment bitte – ich beantworte gerade erst deine letzte Frage.",
            quelle="regelwerk",
        )
    session["_bot_last"] = now

    ctx = student_stats.bot_context(get_db(), session["student_id"])
    from .bot_ai import ask

    antwort, quelle = ask(frage, ctx, allow_ai=not current_app.config.get("TESTING"))
    return jsonify(antwort=antwort, quelle=quelle)


def _pct(part, total):
    return round(min(100, part / total * 100), 1) if total else 0


@bp.route("/meine")
@role_required("student")
def meine():
    """Read-only-Dashboard: eigener Fortschritt + eigene Einträge."""
    db = get_db()
    rows = db.execute(
        "select p.*, u.real_name as reviewer_name from performances p "
        "left join users u on p.reviewed_by = u.id where p.student_id = ? "
        "order by p.performed_on desc, p.id desc",
        (session["student_id"],),
    ).fetchall()

    by_item = {}
    for r in rows:
        by_item.setdefault(r["item_code"], []).append(r)

    progress = []
    o_app = o_tgt = 0
    done_count = 0
    for category, items in CATALOG:
        target = CATEGORY_TARGET.get(category, 0)
        c_app = 0
        item_rows = []
        for it in items:
            ents = by_item.get(it["code"], [])
            appts = sum(
                e["points"] * e["count"] for e in ents if e["status"] == "approved"
            )
            appcnt = sum(e["count"] for e in ents if e["status"] == "approved")
            c_app += appts
            item_rows.append({"item": it, "appts": appts, "appcnt": appcnt})
        app_pct = _pct(c_app, target)
        if target and c_app >= target:
            done_count += 1
        progress.append(
            {
                "category": category,
                "target": target,
                "approved": c_app,
                "app_pct": app_pct,
                "leistungen": item_rows,
            }
        )
        o_app += c_app
        o_tgt += target

    overall = {
        "approved": o_app,
        "target": o_tgt,
        "app_pct": _pct(o_app, o_tgt),
        "done_count": done_count,
        "cat_count": len(progress),
    }
    entries = [r for r in rows if r["status"] == "approved"]
    from .matching import recommend_cases_for_student

    empfehlungen = recommend_cases_for_student(db, session["student_id"])
    return render_template(
        "student_dashboard.html",
        progress=progress,
        entries=entries,
        overall=overall,
        empfehlungen=empfehlungen,
    )
