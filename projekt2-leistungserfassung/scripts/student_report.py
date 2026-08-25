"""Erzeugt Auswertungs-Grafiken als PNG + SVG (aus Code, jederzeit regenerierbar).

    python -m scripts.student_report --all           # alle Studierenden + Kohorte
    python -m scripts.student_report S-0R8P1w         # nur eine Kennung

Schreibt nach docs/reports/:
  _kohorte/vergleich.{png,svg}      alle Studierenden nebeneinander
  _kohorte/matrix.{png,svg}         Kompetenzmatrix Studierende × Kategorien
  <kennung>/{radar,verlauf,fortschritt}.{png,svg}   pro Studierendem

docs/reports/ ist git-ignoriert (studierendenbezogene Daten).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt

from app import charts, create_app
from app.db import get_db

OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "reports"
)


def _save(fig, base):
    fig.savefig(base + ".png", dpi=130, bbox_inches="tight")
    fig.savefig(base + ".svg", bbox_inches="tight")
    plt.close(fig)


def report_for(db, s):
    rows = db.execute(
        "select * from performances where student_id = ?", (s["id"],)
    ).fetchall()
    name = s["real_name"] or s["pseudonym"]
    d = os.path.join(OUT, s["pseudonym"])
    os.makedirs(d, exist_ok=True)
    titles = {
        "radar": f"Kompetenzradar – {name}",
        "verlauf": f"Verlauf über die Semester – {name}",
        "fortschritt": f"Fortschritt je Kategorie – {name}",
    }
    for kind, fn in charts.CHARTS.items():
        _save(fn(rows, title=titles[kind]), os.path.join(d, kind))
    print(f"Report für {name} ({s['pseudonym']}): {d}")


def cohort_report(db):
    students = db.execute("select * from students order by real_name").fetchall()
    stats = []
    for s in students:
        rows = db.execute(
            "select * from performances where student_id = ?", (s["id"],)
        ).fetchall()
        agg = charts.approved_by_category(rows)
        stats.append(
            {
                "name": s["real_name"] or s["pseudonym"],
                "approved": sum(agg.values()),
                "pct": charts.total_pct(rows),
                "cat_pcts": charts.category_pcts(rows),
            }
        )
    d = os.path.join(OUT, "_kohorte")
    os.makedirs(d, exist_ok=True)
    _save(charts.cohort_comparison_figure(stats), os.path.join(d, "vergleich"))
    _save(
        charts.cohort_matrix_figure(
            [x["name"] for x in stats], [x["cat_pcts"] for x in stats]
        ),
        os.path.join(d, "matrix"),
    )
    print(f"Kohorten-Report: {d}")


def main(argv):
    app = create_app()
    with app.app_context():
        db = get_db()
        if not argv or argv[0] == "--all":
            students = db.execute(
                "select * from students order by pseudonym"
            ).fetchall()
            cohort_report(db)
        else:
            students = db.execute(
                "select * from students where pseudonym = ?", (argv[0],)
            ).fetchall()
            if not students:
                raise SystemExit(
                    f"Keine/n Studierende/n mit Kennung '{argv[0]}' gefunden."
                )
        for s in students:
            report_for(db, s)
    print(f"\nFertig – Ausgabe unter {OUT}")


if __name__ == "__main__":
    main(sys.argv[1:])
