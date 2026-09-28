from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import (
    PatientCase,
    PatientCaseIn,
    PatientCaseOut,
    PatientCaseUpdate,
    PatientDetail,
    PatientIn,
    PatientOut,
    PatientUpdate,
    TreatmentCaseOut,
    TreatmentProgress,
)
from ..security import require_write_key
from .treatment_cases import _SELECT as _SELECT_TREATMENT_CASES

router = APIRouter(prefix="/patients", tags=["patients"])

# Der Scalar-Subquery holt je patient_case die zeitlich letzte Behandlung
# (nach treatment_date, dann id), falls es mehrere gibt. treated ist einfach
# "gibt es überhaupt eine" - so lässt sich der Bearbeitungsstand jedes
# geplanten Falls direkt mit ausliefern, ohne einen separaten Aufruf gegen
# /treatment-cases nötig zu machen.
_SELECT_CASES = """
    select
        pc.id,
        pc.patient_id,
        pc.class_id,
        cl.name as class_name,
        c.name as category,
        pc.region,
        pc.min_points,
        pc.max_points,
        pc.difficulty,
        pc.expected_dur_min,
        (t.id is not null) as treated,
        t.id as treatment_case_id,
        t.student_id as treated_by_student_id,
        t.treatment_date as treatment_date
    from patient_cases as pc
    join classes as cl on pc.class_id = cl.id
    join categories as c on cl.category_id = c.id
    left join treatment_cases as t on t.id = (
        select tc2.id from treatment_cases as tc2
        where tc2.patient_case_id = pc.id
        order by tc2.treatment_date desc, tc2.id desc
        limit 1
    )
"""


@router.get("", response_model=list[PatientOut])
def list_patients(db: Session = Depends(get_db)):
    """Alle Patienten, auch ohne geplante Fälle (left join)."""
    query = text(
        """
        select
            p.id,
            p.name,
            p.pseudonym,
            p.age,
            p.category,
            count(pc.id) as case_count
        from patients as p
        left join patient_cases as pc on pc.patient_id = p.id
        group by p.id
        order by p.id;
        """
    )
    rows = db.execute(query).mappings()
    return [PatientOut.model_validate(r) for r in rows]


@router.get("/open-cases", response_model=list[PatientCase])
def list_open_cases(
    class_id: int | None = None,
    category_id: int | None = None,
    db: Session = Depends(get_db),
):
    """Alle noch nicht behandelten geplanten Fälle über alle Patienten -
    die Arbeitsliste, was im Kurs noch an Behandlungen offen ist. Filterbar
    nach Klasse und/oder Kategorie."""
    query = text(
        """
        select
            pc.id,
            p.id as patient_id,
            coalesce(p.pseudonym, p.name) as patient,
            c.name as category,
            pc.class_id,
            cl.name as class_name,
            pc.region,
            pc.min_points,
            pc.max_points,
            pc.difficulty,
            pc.expected_dur_min,
            0 as treated,
            null as treatment_case_id,
            null as treated_by_student_id,
            null as treatment_date
        from patient_cases as pc
        join patients as p on pc.patient_id = p.id
        join classes as cl on pc.class_id = cl.id
        join categories as c on cl.category_id = c.id
        where not exists (
                select 1 from treatment_cases as tc where tc.patient_case_id = pc.id
            )
          and (:class_id is null or pc.class_id = :class_id)
          and (:category_id is null or c.id = :category_id)
        order by p.id, c.id, cl.id, pc.id;
        """
    )
    rows = db.execute(
        query, {"class_id": class_id, "category_id": category_id}
    ).mappings()
    return [PatientCase.model_validate(r) for r in rows]


@router.get("/{patient_id}", response_model=PatientDetail)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    query = text(
        "select id, name, pseudonym, age, category from patients where id = :patient_id"
    )
    row = db.execute(query, {"patient_id": patient_id}).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Patient nicht gefunden")
    cases = db.execute(
        text(_SELECT_CASES + " where pc.patient_id = :patient_id order by c.id, cl.id"),
        {"patient_id": patient_id},
    ).mappings()
    return PatientDetail.model_validate(
        {**row, "cases": [PatientCaseOut.model_validate(r) for r in cases]}
    )


@router.get("/{patient_id}/cases", response_model=list[PatientCase])
def get_patient_cases(
    patient_id: int,
    treated: bool | None = None,
    db: Session = Depends(get_db),
):
    """Geplante Fälle inkl. Behandlungsstatus (treated/treatment_case_id/
    treated_by_student_id/treatment_date) - damit lässt sich pro Patient auf
    einen Blick sehen, was schon behandelt wurde und was noch offen ist.
    ?treated=false liefert nur die offenen, ?treated=true nur die behandelten."""
    query = text(
        """
        select
            pc.id,
            p.id as patient_id,
            coalesce(p.pseudonym, p.name) as patient,
            c.name as category,
            pc.class_id,
            cl.name as class_name,
            pc.region,
            pc.min_points,
            pc.max_points,
            pc.difficulty,
            pc.expected_dur_min,
            (t.id is not null) as treated,
            t.id as treatment_case_id,
            t.student_id as treated_by_student_id,
            t.treatment_date as treatment_date
        from patient_cases as pc
        join patients as p on pc.patient_id = p.id
        join classes as cl on pc.class_id = cl.id
        join categories as c on cl.category_id = c.id
        left join treatment_cases as t on t.id = (
            select tc2.id from treatment_cases as tc2
            where tc2.patient_case_id = pc.id
            order by tc2.treatment_date desc, tc2.id desc
            limit 1
        )
        where p.id = :patient_id
          and (:treated is null or (t.id is not null) = :treated)
        order by c.id, cl.id;
        """
    )
    rows = db.execute(
        query,
        {
            "patient_id": patient_id,
            "treated": None if treated is None else int(treated),
        },
    ).mappings()
    return [PatientCase.model_validate(r) for r in rows]


@router.get("/{patient_id}/treatment-progress", response_model=TreatmentProgress)
def get_treatment_progress(patient_id: int, db: Session = Depends(get_db)):
    """Behandlungsstand auf einen Blick: geplante vs. behandelte vs. offene
    Fälle samt Punkte-Spannen. 404 bei unbekanntem Patienten."""
    _require_patient(patient_id, db)
    row = (
        db.execute(
            text(
                """
            select
                p.id as patient_id,
                coalesce(p.pseudonym, p.name) as patient,
                count(pc.id) as planned_cases,
                coalesce(sum(t.id is not null), 0) as treated_cases,
                coalesce(sum(pc.min_points), 0) as planned_points_min,
                coalesce(sum(pc.max_points), 0) as planned_points_max,
                coalesce(sum(case when t.id is not null then pc.min_points end), 0)
                    as treated_points_min,
                coalesce(sum(case when t.id is not null then pc.max_points end), 0)
                    as treated_points_max,
                max(t.treatment_date) as last_treatment_date
            from patients as p
            left join patient_cases as pc on pc.patient_id = p.id
            left join treatment_cases as t on t.id = (
                select tc2.id from treatment_cases as tc2
                where tc2.patient_case_id = pc.id
                order by tc2.treatment_date desc, tc2.id desc
                limit 1
            )
            where p.id = :patient_id
            group by p.id
            """
            ),
            {"patient_id": patient_id},
        )
        .mappings()
        .first()
    )
    data = dict(row)
    planned, treated = data["planned_cases"], data["treated_cases"]
    data["open_cases"] = planned - treated
    data["progress_pct"] = round(100.0 * treated / planned, 1) if planned else None
    return TreatmentProgress.model_validate(data)


@router.get("/{patient_id}/treatments", response_model=list[TreatmentCaseOut])
def get_patient_treatments(patient_id: int, db: Session = Depends(get_db)):
    """Komplette Behandlungshistorie eines Patienten, chronologisch - Kurzform
    für GET /treatment-cases?patient_id=... ."""
    _require_patient(patient_id, db)
    query = text(
        _SELECT_TREATMENT_CASES
        + " where tc.patient_id = :patient_id order by tc.treatment_date, tc.id;"
    )
    rows = db.execute(query, {"patient_id": patient_id}).mappings()
    return [TreatmentCaseOut.model_validate(r) for r in rows]


def _require_patient(patient_id: int, db: Session) -> None:
    row = db.execute(
        text("select id from patients where id = :patient_id"),
        {"patient_id": patient_id},
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Patient nicht gefunden")


def _check_pseudonym(
    pseudonym: str | None, patient_id: int | None, db: Session
) -> None:
    """409, wenn ein anderer Patient die Kennung schon trägt."""
    if pseudonym is None:
        return
    query = text(
        """
        select id from patients
        where pseudonym = :pseudonym
          and (:patient_id is null or id != :patient_id)
        """
    )
    row = db.execute(query, {"pseudonym": pseudonym, "patient_id": patient_id}).first()
    if row is not None:
        raise HTTPException(
            status_code=409, detail=f"Pseudonym schon vergeben: {pseudonym}"
        )


def _check_class_id(class_id: int | None, db: Session) -> None:
    """422 statt Datenbankfehler, wie bei POST /treatment-cases."""
    if class_id is None:
        raise HTTPException(status_code=422, detail="class_id darf nicht null sein")
    row = db.execute(
        text("select id from classes where id = :id"), {"id": class_id}
    ).first()
    if row is None:
        raise HTTPException(status_code=422, detail=f"Unbekannte class_id: {class_id}")


def _load_case(patient_id: int, case_id: int, db: Session) -> PatientCaseOut:
    query = text(
        _SELECT_CASES + " where pc.id = :case_id and pc.patient_id = :patient_id"
    )
    row = (
        db.execute(query, {"case_id": case_id, "patient_id": patient_id})
        .mappings()
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Fall nicht gefunden")
    return PatientCaseOut.model_validate(row)


@router.post(
    "",
    response_model=PatientDetail,
    status_code=201,
    dependencies=[Depends(require_write_key)],
)
def create_patient(payload: PatientIn, db: Session = Depends(get_db)):
    _check_pseudonym(payload.pseudonym, None, db)
    insert = text(
        """
        insert into patients (name, pseudonym, age, category)
        values (:name, :pseudonym, :age, :category)
        """
    )
    result = db.execute(insert, payload.model_dump())
    db.commit()
    return get_patient(result.lastrowid, db)


@router.patch(
    "/{patient_id}",
    response_model=PatientDetail,
    dependencies=[Depends(require_write_key)],
)
def update_patient(
    patient_id: int, payload: PatientUpdate, db: Session = Depends(get_db)
):
    """Nur gesendete Felder werden geschrieben, ein gesendetes null löscht den Wert."""
    current = (
        db.execute(
            text("select name, pseudonym from patients where id = :patient_id"),
            {"patient_id": patient_id},
        )
        .mappings()
        .first()
    )
    if current is None:
        raise HTTPException(status_code=404, detail="Patient nicht gefunden")
    changes = payload.model_dump(exclude_unset=True)
    merged = {**current, **changes}
    if merged["pseudonym"] is None and merged["name"] is None:
        raise HTTPException(
            status_code=422, detail="pseudonym oder name muss gesetzt bleiben"
        )
    _check_pseudonym(changes.get("pseudonym"), patient_id, db)
    if changes:
        set_clause = ", ".join(f"{field} = :{field}" for field in changes)
        db.execute(
            text(f"update patients set {set_clause} where id = :patient_id"),
            {**changes, "patient_id": patient_id},
        )
        db.commit()
    return get_patient(patient_id, db)


@router.delete(
    "/{patient_id}",
    status_code=204,
    dependencies=[Depends(require_write_key)],
)
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    """Löscht Zuordnung, geplante Fälle und den Patienten. Behandlungsfälle
    bleiben Bestand: hängen welche am Patienten, antwortet die API mit 409."""
    _require_patient(patient_id, db)
    count = db.execute(
        text("select count(*) from treatment_cases where patient_id = :patient_id"),
        {"patient_id": patient_id},
    ).scalar()
    if count:
        raise HTTPException(
            status_code=409,
            detail=f"Patient hängt an {count} Behandlungsfällen und kann nicht gelöscht werden",
        )
    # Reihenfolge wegen pragma foreign_keys=on: erst die verweisenden Zeilen.
    for table in ("patient_assignments", "patient_cases"):
        db.execute(
            text(f"delete from {table} where patient_id = :patient_id"),
            {"patient_id": patient_id},
        )
    db.execute(
        text("delete from patients where id = :patient_id"), {"patient_id": patient_id}
    )
    db.commit()
    return Response(status_code=204)


@router.post(
    "/{patient_id}/cases",
    response_model=PatientCaseOut,
    status_code=201,
    dependencies=[Depends(require_write_key)],
)
def create_patient_case(
    patient_id: int, payload: PatientCaseIn, db: Session = Depends(get_db)
):
    _require_patient(patient_id, db)
    _check_class_id(payload.class_id, db)
    insert = text(
        """
        insert into patient_cases
            (patient_id, class_id, region, min_points, max_points,
             difficulty, expected_dur_min)
        values
            (:patient_id, :class_id, :region, :min_points, :max_points,
             :difficulty, :expected_dur_min)
        """
    )
    result = db.execute(insert, {**payload.model_dump(), "patient_id": patient_id})
    db.commit()
    return _load_case(patient_id, result.lastrowid, db)


@router.patch(
    "/{patient_id}/cases/{case_id}",
    response_model=PatientCaseOut,
    dependencies=[Depends(require_write_key)],
)
def update_patient_case(
    patient_id: int,
    case_id: int,
    payload: PatientCaseUpdate,
    db: Session = Depends(get_db),
):
    """404, wenn der Fall nicht zu diesem Patienten gehört."""
    _load_case(patient_id, case_id, db)
    changes = payload.model_dump(exclude_unset=True)
    if "class_id" in changes:
        _check_class_id(changes["class_id"], db)
    if changes:
        set_clause = ", ".join(f"{field} = :{field}" for field in changes)
        db.execute(
            text(f"update patient_cases set {set_clause} where id = :case_id"),
            {**changes, "case_id": case_id},
        )
        db.commit()
    return _load_case(patient_id, case_id, db)


@router.delete(
    "/{patient_id}/cases/{case_id}",
    status_code=204,
    dependencies=[Depends(require_write_key)],
)
def delete_patient_case(patient_id: int, case_id: int, db: Session = Depends(get_db)):
    """409, wenn der Fall schon behandelt wurde: die Behandlungen verweisen per
    patient_case_id darauf. Erst die Behandlung löschen oder die Verknüpfung
    lösen (PATCH /treatment-cases/{id} mit patient_case_id=null)."""
    _load_case(patient_id, case_id, db)
    count = db.execute(
        text("select count(*) from treatment_cases where patient_case_id = :case_id"),
        {"case_id": case_id},
    ).scalar()
    if count:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Fall wurde bereits {count}x behandelt und kann nicht gelöscht "
                "werden. Erst die Behandlung(en) löschen oder die Verknüpfung lösen."
            ),
        )
    db.execute(
        text("delete from patient_cases where id = :case_id"), {"case_id": case_id}
    )
    db.commit()
    return Response(status_code=204)
