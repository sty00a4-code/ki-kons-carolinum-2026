"""Berechnet den Fortschritt eines Studierenden – read-only.

Wird von der Studenten-Ansicht und vom Demo-Bot genutzt. WICHTIG: Alle
Funktionen sind an EINE student_id gebunden (die des eingeloggten Studierenden).
Es gibt keinen Weg, hierüber Daten anderer Studierender zu laden – der Demo-Bot
bekommt ausschließlich das Ergebnis für die eigene student_id.
"""

from .catalog import CATALOG, CATEGORY_TARGET, SEMESTERS, TOTAL_TARGET


def progress(db, student_id):
    """Fortschritt je Kategorie (nur genehmigte/eingetragene Leistungen)."""
    rows = db.execute(
        "select category, points, count from performances "
        "where student_id = ? and status = 'approved'",
        (student_id,),
    ).fetchall()
    agg = {c: 0.0 for c, _ in CATALOG}
    for r in rows:
        if r["category"] in agg:
            agg[r["category"]] += r["points"] * r["count"]

    cats = []
    for category, _items in CATALOG:
        target = CATEGORY_TARGET.get(category, 0)
        approved = agg[category]
        pct = min(100.0, approved / target * 100) if target else 0.0
        cats.append(
            {
                "name": category,
                "approved": round(approved, 1),
                "target": target,
                "pct": round(pct),
                "missing": round(max(0.0, target - approved), 1),
                "done": approved >= target,
            }
        )
    total = sum(agg.values())
    return {
        "cats": cats,
        "total": round(total, 1),
        "target": TOTAL_TARGET,
        "overall": round(min(100.0, total / TOTAL_TARGET * 100)),
        "done_count": sum(1 for c in cats if c["done"]),
        "cat_count": len(cats),
    }


def semester_verlauf(db, student_id):
    """Kompetenzentwicklung im Zeitverlauf (Folie Schritt 8): Punkte je
    Semester + kumulierte Ziel-Erreichung – die 'Lernkurve'."""
    rows = db.execute(
        "select semester, sum(points*count) as p from performances "
        "where student_id = ? and status = 'approved' group by semester",
        (student_id,),
    ).fetchall()
    per_sem = {r["semester"]: r["p"] for r in rows}
    verlauf, cum = [], 0.0
    for sem in SEMESTERS:
        p = per_sem.get(sem)
        if p is None:
            continue
        cum += p
        verlauf.append(
            {
                "semester": sem,
                "punkte": round(p, 1),
                "kumuliert_pct": round(min(100.0, cum / TOTAL_TARGET * 100)),
            }
        )
    return verlauf


def bot_context(db, student_id):
    """Kompakter Datensatz NUR für den eingeloggten Studierenden (Demo-Bot)."""
    p = progress(db, student_id)
    weakest = sorted([c for c in p["cats"] if not c["done"]], key=lambda c: c["pct"])[
        :3
    ]
    # Import hier (nicht am Modulkopf): matching importiert progress von hier.
    from .matching import recommend_cases_for_student

    try:
        recs = recommend_cases_for_student(db, student_id)
    except Exception:
        recs = []
    return {
        "overall": p["overall"],
        "total": p["total"],
        "target": p["target"],
        "done_count": p["done_count"],
        "cat_count": p["cat_count"],
        "weakest": [
            {"name": c["name"], "pct": c["pct"], "missing": c["missing"]}
            for c in weakest
        ],
        "done": [c["name"] for c in p["cats"] if c["done"]],
        "verlauf": semester_verlauf(db, student_id),
        "empfehlungen": [
            {
                "ref": r["case"]["case_ref"],
                "match": r["match_pct"],
                "beitrag": r["beitrag"],
                "begruendung": r["begruendung"],
            }
            for r in recs
        ],
    }
