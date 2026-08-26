"""Auswertung für Doktoranden: Kohorten-Vergleich + Entwicklung pro Studierendem.

Alle Grafiken kommen aus app/charts.py (matplotlib) und basieren auf den
GENEHMIGTEN Daten in der SQLite-Datenbank – dieselbe DB, in die Studierende
ihre Einträge sofort beim Speichern schreiben. Nach jeder Genehmigung sind
die Grafiken beim nächsten Seitenaufruf aktuell.

Nur für Doktoranden/Admins zugänglich; hier werden bewusst KLARNAMEN gezeigt
(der Prüfer kennt alle Studierenden). Studierende erreichen diese Routen nicht.
"""

from flask import Blueprint, Response, abort, render_template

from . import charts
from .catalog import TOTAL_TARGET
from .db import get_db
from .security import role_required

bp = Blueprint("analysis", __name__)


def _png(fig):
    return Response(charts.figure_to_png(fig), mimetype="image/png")


def _display_name(s):
    return s["real_name"] or s["pseudonym"]


def _cohort_stats():
    """Fortschritts-Statistik für ALLE Studierenden (Klarnamen)."""
    db = get_db()
    students = db.execute(
        "select * from students order by real_name, pseudonym"
    ).fetchall()
    stats = []
    for s in students:
        rows = db.execute(
            "select * from performances where student_id = ?", (s["id"],)
        ).fetchall()
        agg = charts.approved_by_category(rows)
        approved = sum(agg.values())
        stats.append(
            {
                "s": s,
                "name": _display_name(s),
                "approved": approved,
                "pct": charts.total_pct(rows),
                "cat_pcts": charts.category_pcts(rows),
                "pending": sum(1 for r in rows if r["status"] == "submitted"),
            }
        )
    return stats


def _student_rows(pseudonym):
    db = get_db()
    s = db.execute(
        "select * from students where pseudonym = ?", (pseudonym,)
    ).fetchone()
    if s is None:
        abort(404)
    rows = db.execute(
        "select * from performances where student_id = ?", (s["id"],)
    ).fetchall()
    return s, rows


@bp.route("/auswertung")
@role_required("doktorand", "admin")
def auswertung():
    stats = sorted(_cohort_stats(), key=lambda x: -x["pct"])
    return render_template("auswertung.html", stats=stats, total_target=TOTAL_TARGET)


@bp.route("/auswertung/vergleich.png")
@role_required("doktorand", "admin")
def cohort_comparison():
    return _png(charts.cohort_comparison_figure(_cohort_stats()))


@bp.route("/auswertung/matrix.png")
@role_required("doktorand", "admin")
def cohort_matrix():
    stats = _cohort_stats()
    return _png(
        charts.cohort_matrix_figure(
            [x["name"] for x in stats], [x["cat_pcts"] for x in stats]
        )
    )


@bp.route("/student/<pseudonym>/<kind>.png")
@role_required("doktorand", "admin")
def student_chart(pseudonym, kind):
    """Grafik pro Studierendem: kind ∈ {radar, verlauf, fortschritt}."""
    if kind not in charts.CHARTS:
        abort(404)
    s, rows = _student_rows(pseudonym)
    titles = {
        "radar": f"Kompetenzradar – {_display_name(s)}",
        "verlauf": f"Verlauf über die Semester – {_display_name(s)}",
        "fortschritt": f"Fortschritt je Kategorie – {_display_name(s)}",
    }
    return _png(charts.CHARTS[kind](rows, title=titles[kind]))
