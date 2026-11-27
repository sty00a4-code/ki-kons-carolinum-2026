"""Matching-Logik: welche Patienten würden welchem Studenten am meisten
helfen, ihre offenen Anforderungen aus dem Leistungskatalog zu erfüllen.

Basis ist classes.min_points / min_count vs. die Summe aus students_classes
über ALLE Semester (nicht pro Semester). Matcht auf Klassen-Ebene, nicht auf
Kompetenzen - die Tabellen dafür sind noch leer.
"""

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from .hungarian import solve_max

# Kennung von Score-Logik + Zuordnungsverfahren, damit Empfehlungen sich
# später zuordnen lassen. v1: Score je Klasse, greedy. v2: derselbe Score,
# Zuordnung per Hungarian-Algorithmus.
ALGORITHM_VERSION = "class-match-v1"
HUNGARIAN_VERSION = "class-match-v2"
STRATEGIES = ("hungarian", "greedy")


@dataclass
class ClassDeficit:
    class_id: int
    class_name: str
    category: str
    min_points: float | None
    min_count: int | None
    achieved_points: float
    achieved_count: int
    deficit_points: float
    deficit_count: int


@dataclass
class PatientContribution:
    patient_id: int
    patient_name: str
    class_id: int
    avg_points: float
    case_count: int


def find_missing_classes(student_id: int, db: Session) -> list[ClassDeficit]:
    """Alle Klassen, bei denen der Student sein Punkte- oder Anzahl-Soll,
    kumuliert über alle Semester, noch nicht erreicht hat. Klassen ohne
    definiertes Soll (min_points und min_count beide NULL) werden nie als
    fehlend gewertet, da es dafür schlicht keine Vorgabe gibt."""
    rows = (
        db.execute(
            text("""
            select
                cl.id as class_id,
                cl.name as class_name,
                c.name as category,
                cl.min_points,
                cl.min_count,
                coalesce(sum(sc.points), 0) as achieved_points,
                coalesce(sum(sc.count), 0) as achieved_count
            from classes as cl
            join categories as c on cl.category_id = c.id
            left join students_classes as sc
                on sc.class_id = cl.id and sc.student_id = :student_id
            group by cl.id
            """),
            {"student_id": student_id},
        )
        .mappings()
        .all()
    )

    deficits = []
    for r in rows:
        min_points = r["min_points"]
        min_count = r["min_count"]
        deficit_points = (
            max(0.0, float(min_points) - r["achieved_points"])
            if min_points is not None
            else 0.0
        )
        deficit_count = (
            max(0, int(min_count) - r["achieved_count"]) if min_count is not None else 0
        )

        if deficit_points > 0 or deficit_count > 0:
            deficits.append(
                ClassDeficit(
                    class_id=r["class_id"],
                    class_name=r["class_name"],
                    category=r["category"],
                    min_points=min_points,
                    min_count=min_count,
                    achieved_points=r["achieved_points"],
                    achieved_count=r["achieved_count"],
                    deficit_points=deficit_points,
                    deficit_count=deficit_count,
                )
            )
    return deficits


def get_patient_contributions(db: Session) -> list[PatientContribution]:
    """Was jeder Patient je Klasse an Punkten/Fällen beisteuern könnte:
    Durchschnitt aus (min_points+max_points)/2 je patient_cases-Zeile,
    plus Anzahl der Fälle, gruppiert nach Patient x Klasse."""
    rows = db.execute(text("""
            select
                p.id as patient_id,
                coalesce(p.pseudonym, p.name) as patient_name,
                pc.class_id,
                avg((pc.min_points + pc.max_points) / 2.0) as avg_points,
                count(*) as case_count
            from patient_cases as pc
            join patients as p on pc.patient_id = p.id
            group by p.id, pc.class_id
            """)).mappings().all()
    return [
        PatientContribution(
            patient_id=r["patient_id"],
            patient_name=r["patient_name"],
            class_id=r["class_id"],
            avg_points=r["avg_points"] or 0.0,
            case_count=r["case_count"],
        )
        for r in rows
    ]


def score_patient_for_deficits(
    contributions: list[PatientContribution], deficits: list[ClassDeficit]
) -> tuple[float, list[dict]]:
    """Score = gedeckelte Punkte + gedeckelte Fallanzahl, die der Patient zu
    den offenen Klassen des Studenten beitragen könnte. Deckelung (min mit
    dem verbleibenden Defizit) verhindert, dass ein Patient nur wegen eines
    einzigen, stark überschüssigen Falls hoch bewertet wird - Patienten, die
    mehrere Lücken gleichzeitig schließen, werden dadurch bevorzugt."""
    deficit_by_class = {d.class_id: d for d in deficits}
    matched_classes = []
    score = 0.0

    for contrib in contributions:
        deficit = deficit_by_class.get(contrib.class_id)
        if deficit is None:
            continue

        covered_points = 0.0
        if deficit.deficit_points > 0:
            covered_points = min(
                contrib.avg_points * contrib.case_count, deficit.deficit_points
            )

        covered_count = 0
        if deficit.deficit_count > 0:
            covered_count = min(contrib.case_count, deficit.deficit_count)

        if covered_points <= 0 and covered_count <= 0:
            continue

        score += covered_points + covered_count
        matched_classes.append(
            {
                "class_id": contrib.class_id,
                "class_name": deficit.class_name,
                "category": deficit.category,
                "covered_points": round(covered_points, 2),
                "covered_count": covered_count,
                "available_cases": contrib.case_count,
                # Erklärung: wie groß die Lücke VOR diesem Patienten war.
                "deficit_points_before": round(deficit.deficit_points, 2),
                "deficit_count_before": deficit.deficit_count,
            }
        )

    return score, matched_classes


def rank_patients_for_student(
    student_id: int, db: Session, limit: int = 5
) -> list[dict]:
    """Für einen Studenten: Patienten sortiert nach Nutzen für die offenen
    Anforderungen. Genau das `suggest_patient_assignment` aus dem Outline."""
    deficits = find_missing_classes(student_id, db)
    if not deficits:
        return []

    all_contributions = get_patient_contributions(db)
    by_patient: dict[int, list[PatientContribution]] = {}
    names: dict[int, str] = {}
    for c in all_contributions:
        by_patient.setdefault(c.patient_id, []).append(c)
        names[c.patient_id] = c.patient_name

    results = []
    for patient_id, contributions in by_patient.items():
        score, matched_classes = score_patient_for_deficits(contributions, deficits)
        if score <= 0:
            continue
        results.append(
            {
                "patient_id": patient_id,
                "patient_name": names[patient_id],
                "score": round(score, 2),
                "algorithm_version": ALGORITHM_VERSION,
                "matched_classes": matched_classes,
            }
        )

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


def suggest_global_matching(
    db: Session, strategy: str = "hungarian", max_per_student: int | None = None
) -> dict:
    """Gesamtzuordnung aller Patienten zu Studenten.

    strategy "hungarian" (Standard): rundenweise optimal, siehe
    suggest_global_matching_hungarian. strategy "greedy": das frühere
    Verfahren, nur noch zum Vergleich."""
    if strategy == "greedy":
        return suggest_global_matching_greedy(db, max_per_student)
    if strategy == "hungarian":
        return suggest_global_matching_hungarian(db, max_per_student)
    raise ValueError(f"Unbekannte strategy: {strategy}")


def _load_matching_inputs(db: Session):
    student_ids = (
        db.execute(text("select id from students order by id")).scalars().all()
    )
    deficits_by_student = {sid: find_missing_classes(sid, db) for sid in student_ids}
    contributions_by_patient: dict[int, list[PatientContribution]] = {}
    patient_names: dict[int, str] = {}
    for c in get_patient_contributions(db):
        contributions_by_patient.setdefault(c.patient_id, []).append(c)
        patient_names[c.patient_id] = c.patient_name
    return deficits_by_student, contributions_by_patient, patient_names


def _reduce_deficits(deficits: list[ClassDeficit], matched_classes: list[dict]):
    """Zieht ab, was der zugewiesene Patient abdeckt; erledigte Lücken fallen weg."""
    by_class = {d.class_id: d for d in deficits}
    for m in matched_classes:
        d = by_class.get(m["class_id"])
        if d:
            d.deficit_points = max(0.0, d.deficit_points - m["covered_points"])
            d.deficit_count = max(0, d.deficit_count - m["covered_count"])
    return [d for d in deficits if d.deficit_points > 0 or d.deficit_count > 0]


def suggest_global_matching_hungarian(
    db: Session, max_per_student: int | None = None
) -> dict:
    """Optimale Zuordnung per Hungarian-Algorithmus, rundenweise.

    Jede Runde: Matrix Student x freier Patient (Score aus
    score_patient_for_deficits), maximale Summe über alle Paare - anders als
    Greedy, das sich am besten Einzelpaar verbaut. Da es mehr Patienten als
    Studierende geben kann, läuft danach eine weitere Runde mit den
    reduzierten Defiziten und den übrigen Patienten, bis kein Paar mehr einen
    positiven Score hat. max_per_student begrenzt Zuweisungen je Student über
    alle Runden (None = unbegrenzt); die Runde steht als "round" dabei.

    Grenze: jede Runde ist optimal, die Abfolge der Runden nicht zwingend."""
    deficits_by_student, contributions_by_patient, patient_names = _load_matching_inputs(db)
    unassigned = set(contributions_by_patient)
    assigned_count = {sid: 0 for sid in deficits_by_student}
    assignments: list[dict] = []
    round_no = 0

    while unassigned:
        students = [
            sid
            for sid, deficits in deficits_by_student.items()
            if deficits and (max_per_student is None or assigned_count[sid] < max_per_student)
        ]
        patients = sorted(unassigned)
        if not students or not patients:
            break
        matrix, details = [], {}
        for r, sid in enumerate(students):
            row = []
            for c, pid in enumerate(patients):
                score, matched = score_patient_for_deficits(
                    contributions_by_patient[pid], deficits_by_student[sid]
                )
                row.append(score)
                details[(r, c)] = matched
            matrix.append(row)
        pairs = solve_max(matrix)
        if not pairs:
            break
        round_no += 1
        for r, c in pairs:
            sid, pid, matched = students[r], patients[c], details[(r, c)]
            assignments.append(
                {
                    "student_id": sid,
                    "patient_id": pid,
                    "patient_name": patient_names[pid],
                    "score": round(matrix[r][c], 2),
                    "algorithm_version": HUNGARIAN_VERSION,
                    "round": round_no,
                    "matched_classes": matched,
                }
            )
            unassigned.discard(pid)
            assigned_count[sid] += 1
            deficits_by_student[sid] = _reduce_deficits(deficits_by_student[sid], matched)

    return {
        "algorithm_version": HUNGARIAN_VERSION,
        "strategy": "hungarian",
        "total_score": round(sum(a["score"] for a in assignments), 2),
        "assignments": assignments,
        "unmatched_patients": [
            {"patient_id": pid, "patient_name": patient_names[pid]}
            for pid in sorted(unassigned)
        ],
    }


def suggest_global_matching_greedy(
    db: Session, max_per_student: int | None = None
) -> dict:
    """Früheres Verfahren (greedy, nicht global optimal): in jedem Schritt wird
    das aktuell beste (Student, Patient)-Paar zugewiesen; danach werden die
    Defizite des Studenten um das reduziert, was der Patient abdeckt, und der
    Patient steht nicht mehr zur Verfügung."""
    deficits_by_student, contributions_by_patient, patient_names = _load_matching_inputs(db)
    unassigned_patients = set(contributions_by_patient)
    assigned_count = {sid: 0 for sid in deficits_by_student}
    assignments = []

    while unassigned_patients:
        best = None  # (score, student_id, patient_id, matched_classes)
        for sid, deficits in deficits_by_student.items():
            if not deficits or (
                max_per_student is not None and assigned_count[sid] >= max_per_student
            ):
                continue
            for pid in unassigned_patients:
                score, matched_classes = score_patient_for_deficits(
                    contributions_by_patient[pid], deficits
                )
                if score <= 0:
                    continue
                if best is None or score > best[0]:
                    best = (score, sid, pid, matched_classes)

        if best is None:
            break  # keine verbleibende Zuordnung bringt noch Nutzen

        score, sid, pid, matched_classes = best
        assignments.append(
            {
                "student_id": sid,
                "patient_id": pid,
                "patient_name": patient_names[pid],
                "score": round(score, 2),
                "algorithm_version": ALGORITHM_VERSION,
                "matched_classes": matched_classes,
            }
        )
        unassigned_patients.remove(pid)
        assigned_count[sid] += 1
        deficits_by_student[sid] = _reduce_deficits(deficits_by_student[sid], matched_classes)

    return {
        "algorithm_version": ALGORITHM_VERSION,
        "strategy": "greedy",
        "total_score": round(sum(a["score"] for a in assignments), 2),
        "assignments": assignments,
        "unmatched_patients": [
            {"patient_id": pid, "patient_name": patient_names[pid]}
            for pid in sorted(unassigned_patients)
        ],
    }
