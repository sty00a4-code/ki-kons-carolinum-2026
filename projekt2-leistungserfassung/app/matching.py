"""Fall-Empfehlung (Matching) – Kick-Off-Folie Dashboard D / "Fallempfehlung".

Transparente, erklärbare Logik (bewusst KEIN Blackbox-Modell):
Ein Fall bietet Katalog-Leistungen mit Punkten. Für eine/n Studierende/n
zählt, wie viele dieser Punkte ECHTE Lücken schließen (fehlende Punkte bis
zur Mindestanforderung je Kategorie).

    Match-% = geschlossene Lückenpunkte / Fallpunkte * 100

Kompetenzbeitrag: hoch (>= 10 P Lückenschluss), mittel (>= 4), gering (> 0).
Die Begründung nennt die Kategorien, in denen der Fall Lücken schließt –
damit Lehrende jede Empfehlung nachvollziehen können (human validierbar,
Phase-4-Prinzip). Ausbaustufe (bewusst offen): Schwierigkeits-Passung an den
individuellen Stand, sobald die Lehrenden-Kartierung konsentiert ist.
"""

from .student_stats import progress

BEITRAG = [(10, "hoch"), (4, "mittel"), (0.000001, "gering")]


def _beitrag(covered):
    for schwelle, label in BEITRAG:
        if covered >= schwelle:
            return label
    return "kein"


def score_case(case_items, gaps):
    """Bewertet einen Fall gegen die Lücken (dict Kategorie -> fehlende Punkte).

    case_items: iterable mit .category und .points (oder dicts).
    Rückgabe: dict(match_pct, covered, case_points, beitrag, begruendung).
    """
    remaining = dict(gaps)
    covered = 0.0
    case_points = 0.0
    closed = {}
    for it in case_items:
        cat = it["category"]
        pts = float(it["points"])
        case_points += pts
        take = min(pts, max(0.0, remaining.get(cat, 0.0)))
        if take > 0:
            covered += take
            closed[cat] = closed.get(cat, 0.0) + take
            remaining[cat] = remaining.get(cat, 0.0) - take
    match_pct = round(covered / case_points * 100) if case_points else 0
    begruendung = (
        " · ".join(
            f"{cat}: {pts:g} P"
            for cat, pts in sorted(closed.items(), key=lambda kv: -kv[1])
        )
        or "schließt keine offene Lücke"
    )
    return {
        "match_pct": match_pct,
        "covered": round(covered, 1),
        "case_points": round(case_points, 1),
        "beitrag": _beitrag(covered),
        "begruendung": begruendung,
    }


def student_gaps(db, student_id):
    """Kategorie -> fehlende Punkte bis zur Mindestanforderung."""
    p = progress(db, student_id)
    return {c["name"]: c["missing"] for c in p["cats"]}


def _case_items(db, case_id):
    return db.execute(
        "select * from patient_case_items where case_id = ?", (case_id,)
    ).fetchall()


def open_cases(db):
    return db.execute(
        "select * from patient_cases where status = 'offen' order by created_at desc, id desc"
    ).fetchall()


def recommend_cases_for_student(db, student_id, limit=3):
    """Top-Fälle für eine/n Studierende/n (Dashboard D: 'Empfohlene Patientenfälle')."""
    gaps = student_gaps(db, student_id)
    recs = []
    for case in open_cases(db):
        items = _case_items(db, case["id"])
        s = score_case(items, gaps)
        if s["covered"] <= 0:
            continue
        # Schlüssel heißt bewusst nicht "items" (Jinja: kollidiert mit dict.items)
        recs.append(dict(case=case, leistungen=items, **s))
    recs.sort(key=lambda r: (-r["covered"], -r["match_pct"]))
    return recs[:limit]


def best_students_for_case(db, case, limit=3):
    """Beste Studierende für einen Fall (Folie 4 Schritt 6: 'Bester Match')."""
    items = _case_items(db, case["id"])
    ranked = []
    for s in db.execute("select * from students order by id").fetchall():
        sc = score_case(items, student_gaps(db, s["id"]))
        ranked.append(dict(student=s, **sc))
    ranked.sort(key=lambda r: (-r["covered"], -r["match_pct"]))
    return ranked[:limit]


def kohorten_context(db):
    """Kompakter Kohorten-Datensatz für den Lehrenden-Bot (Klarnamen erlaubt –
    Lehrende sehen sie ohnehin überall in der App)."""
    from .student_stats import semester_verlauf

    students = []
    for s in db.execute("select * from students order by id").fetchall():
        p = progress(db, s["id"])
        weakest = sorted(
            [c for c in p["cats"] if not c["done"]], key=lambda c: c["pct"]
        )[:3]
        students.append(
            {
                "name": s["real_name"] or s["pseudonym"],
                "gesamt_pct": p["overall"],
                "punkte": p["total"],
                "ziel": p["target"],
                "erfuellte_kategorien": p["done_count"],
                "kategorien": p["cat_count"],
                "groesste_luecken": [
                    {"kategorie": c["name"], "pct": c["pct"], "fehlend": c["missing"]}
                    for c in weakest
                ],
                "lernkurve": semester_verlauf(db, s["id"]),
            }
        )
    faelle = []
    for case in open_cases(db):
        best = best_students_for_case(db, case, limit=1)
        b = best[0] if best else None
        faelle.append(
            {
                "fall": case["case_ref"],
                "beschreibung": case["description"],
                "schwierigkeit": case["difficulty"],
                "dauer_min": case["est_minutes"],
                "empfohlen": (
                    {
                        "name": b["student"]["real_name"] or b["student"]["pseudonym"],
                        "match_pct": b["match_pct"],
                        "begruendung": b["begruendung"],
                    }
                    if b and b["covered"] > 0
                    else None
                ),
            }
        )
    return {"studierende": students, "offene_faelle": faelle}
