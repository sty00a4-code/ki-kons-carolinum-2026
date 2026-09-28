import pytest

STUDENT = 0
PATIENT = 0


def _first_planned_case(client, patient_id=PATIENT):
    cases = client.get(f"/patients/{patient_id}/cases").json()
    assert cases, "Testdaten: Patient braucht geplante Fälle"
    return cases[0]


def _category_points(client, student_id, name):
    rows = client.get(f"/students/{student_id}/category-progress").json()
    return next((r["total_points"] for r in rows if r["category"] == name), None)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


# ------------------------- Kategorien direkt bepunkten -------------------------


def test_category_points_add_to_class_points(client):
    category = client.get("/categories").json()[0]
    before = _category_points(client, STUDENT, category["name"]) or 0

    response = client.put(
        f"/categories/{category['id']}/points",
        json={"student_id": STUDENT, "semester": "2026SoSe", "points": 5},
    )
    assert response.status_code == 200
    assert _category_points(client, STUDENT, category["name"]) == before + 5


def test_category_points_upsert_replaces_instead_of_adding(client):
    category = client.get("/categories").json()[0]
    url = f"/categories/{category['id']}/points"
    for value in (5, 9):
        client.put(
            url, json={"student_id": STUDENT, "semester": "2026SoSe", "points": value}
        )
    direct = client.get(f"/students/{STUDENT}/category-points").json()
    mine = [r for r in direct if r["category_id"] == category["id"]]
    assert [r["points"] for r in mine] == [9]


def test_category_without_any_class_rows_still_shows_up(client, db_session):
    from sqlalchemy import text

    # Eigene Kategorie ohne jede Klasse, unabhängig von den Testdaten.
    db_session.execute(
        text(
            "insert into categories (id, name, min_points) values (900, 'Nur direkt', 10)"
        )
    )
    db_session.commit()
    assert _category_points(client, STUDENT, "Nur direkt") is None

    client.put(
        "/categories/900/points",
        json={"student_id": STUDENT, "semester": "2026SoSe", "points": 3},
    )
    row = next(
        r
        for r in client.get(f"/students/{STUDENT}/category-progress").json()
        if r["category"] == "Nur direkt"
    )
    assert row["total_points"] == 3
    assert row["done"] is False
    assert row["progress_pct"] == 30.0


def test_category_points_delete_restores_previous_total(client):
    category = client.get("/categories").json()[0]
    before = _category_points(client, STUDENT, category["name"]) or 0
    url = f"/categories/{category['id']}/points"
    client.put(url, json={"student_id": STUDENT, "semester": "2026SoSe", "points": 5})

    response = client.delete(
        url, params={"student_id": STUDENT, "semester": "2026SoSe"}
    )
    assert response.status_code == 204
    assert (_category_points(client, STUDENT, category["name"]) or 0) == before
    again = client.delete(url, params={"student_id": STUDENT, "semester": "2026SoSe"})
    assert again.status_code == 404


def test_category_points_validation(client):
    category_id = client.get("/categories").json()[0]["id"]
    unknown_category = client.put(
        "/categories/9999/points",
        json={"student_id": STUDENT, "semester": "2026SoSe", "points": 1},
    )
    assert unknown_category.status_code == 404
    unknown_student = client.put(
        f"/categories/{category_id}/points",
        json={"student_id": 9999, "semester": "2026SoSe", "points": 1},
    )
    assert unknown_student.status_code == 422
    bad_semester = client.put(
        f"/categories/{category_id}/points",
        json={"student_id": STUDENT, "semester": "2026", "points": 1},
    )
    assert bad_semester.status_code == 422


def test_analysis_trajectory_counts_direct_category_points(client, db_session):
    from app.routers.analysis import build_learning_trajectory

    category = client.get("/categories").json()[0]

    def total(trajectory):
        return sum(
            r["points"]
            for r in trajectory["category_progress"]
            if r["category"] == category["name"]
        )

    before = total(build_learning_trajectory(STUDENT, db_session))
    client.put(
        f"/categories/{category['id']}/points",
        json={"student_id": STUDENT, "semester": "2026SoSe", "points": 4},
    )
    after = total(build_learning_trajectory(STUDENT, db_session))
    assert after == before + 4


# ------------------------------ Behandlungen tracken ------------------------------


def test_treating_a_planned_case_marks_it_treated(client):
    case = _first_planned_case(client)
    assert case["treated"] is False

    response = client.post(
        "/treatment-cases",
        json={
            "student_id": STUDENT,
            "class_id": case["class_id"],
            "patient_case_id": case["id"],
            "semester": "2026SoSe",
            "treatment_date": "2026-05-01",
        },
    )
    assert response.status_code == 201
    created = response.json()
    assert created["patient_id"] == PATIENT  # automatisch vom Fall übernommen
    assert created["patient_case_id"] == case["id"]

    after = next(
        c
        for c in client.get(f"/patients/{PATIENT}/cases").json()
        if c["id"] == case["id"]
    )
    assert after["treated"] is True
    assert after["treated_by_student_id"] == STUDENT
    assert after["treatment_date"] == "2026-05-01"


def test_treatment_history_and_progress_per_patient(client):
    case = _first_planned_case(client)
    before = client.get(f"/patients/{PATIENT}/treatment-progress").json()
    assert before["treated_cases"] == 0
    assert before["open_cases"] == before["planned_cases"] > 0
    assert before["progress_pct"] == 0

    client.post(
        "/treatment-cases",
        json={
            "student_id": STUDENT,
            "class_id": case["class_id"],
            "patient_case_id": case["id"],
            "semester": "2026SoSe",
            "treatment_date": "2026-05-01",
        },
    )
    after = client.get(f"/patients/{PATIENT}/treatment-progress").json()
    assert after["treated_cases"] == 1
    assert after["open_cases"] == before["planned_cases"] - 1
    assert after["last_treatment_date"] == "2026-05-01"

    history = client.get(f"/patients/{PATIENT}/treatments").json()
    assert len(history) == 1
    assert (
        client.get("/treatment-cases", params={"patient_id": PATIENT}).json() == history
    )
    assert client.get("/treatment-cases", params={"patient_id": 1}).json() == []


def test_treated_filter_and_open_cases_worklist(client):
    case = _first_planned_case(client)
    client.post(
        "/treatment-cases",
        json={
            "student_id": STUDENT,
            "class_id": case["class_id"],
            "patient_case_id": case["id"],
            "semester": "2026SoSe",
        },
    )
    open_ids = {
        c["id"]
        for c in client.get(
            f"/patients/{PATIENT}/cases", params={"treated": False}
        ).json()
    }
    done_ids = {
        c["id"]
        for c in client.get(
            f"/patients/{PATIENT}/cases", params={"treated": True}
        ).json()
    }
    assert done_ids == {case["id"]}
    assert case["id"] not in open_ids

    worklist = client.get("/patients/open-cases").json()
    assert case["id"] not in {c["id"] for c in worklist}
    assert all(c["treated"] is False for c in worklist)
    by_class = client.get(
        "/patients/open-cases", params={"class_id": case["class_id"]}
    ).json()
    assert all(c["class_id"] == case["class_id"] for c in by_class)


def test_mismatching_or_unknown_patient_case_is_rejected(client):
    case = _first_planned_case(client)
    mismatch = client.post(
        "/treatment-cases",
        json={
            "student_id": STUDENT,
            "class_id": case["class_id"],
            "patient_id": 3,
            "patient_case_id": case["id"],
            "semester": "2026SoSe",
        },
    )
    assert mismatch.status_code == 422
    unknown = client.post(
        "/treatment-cases",
        json={
            "student_id": STUDENT,
            "class_id": case["class_id"],
            "patient_case_id": 9999,
            "semester": "2026SoSe",
        },
    )
    assert unknown.status_code == 422


def test_patch_treatment_case_and_unlink(client):
    case = _first_planned_case(client)
    created = client.post(
        "/treatment-cases",
        json={
            "student_id": STUDENT,
            "class_id": case["class_id"],
            "patient_case_id": case["id"],
            "semester": "2026SoSe",
        },
    ).json()
    url = f"/treatment-cases/{created['id']}"

    patched = client.patch(
        url, json={"notes": "korrigiert", "treatment_date": "2026-06-02"}
    )
    assert patched.status_code == 200
    assert patched.json()["notes"] == "korrigiert"
    assert patched.json()["patient_case_id"] == case["id"]  # unverändert

    unlinked = client.patch(url, json={"patient_case_id": None})
    assert unlinked.status_code == 200
    assert unlinked.json()["patient_case_id"] is None
    refreshed = next(
        c
        for c in client.get(f"/patients/{PATIENT}/cases").json()
        if c["id"] == case["id"]
    )
    assert refreshed["treated"] is False

    assert client.patch(url, json={"semester": None}).status_code == 422
    assert client.patch(url, json={"semester": "abc"}).status_code == 422
    assert client.patch("/treatment-cases/9999", json={"notes": "x"}).status_code == 404


def test_patch_with_conflicting_patient_is_rejected(client):
    case = _first_planned_case(client)
    created = client.post(
        "/treatment-cases",
        json={
            "student_id": STUDENT,
            "class_id": case["class_id"],
            "patient_case_id": case["id"],
            "semester": "2026SoSe",
        },
    ).json()
    response = client.patch(f"/treatment-cases/{created['id']}", json={"patient_id": 3})
    assert response.status_code == 422


def test_delete_treatment_case_reopens_planned_case(client):
    case = _first_planned_case(client)
    created = client.post(
        "/treatment-cases",
        json={
            "student_id": STUDENT,
            "class_id": case["class_id"],
            "patient_case_id": case["id"],
            "semester": "2026SoSe",
        },
    ).json()
    assert client.delete(f"/treatment-cases/{created['id']}").status_code == 204
    assert client.get(f"/treatment-cases/{created['id']}").status_code == 404
    reopened = next(
        c
        for c in client.get(f"/patients/{PATIENT}/cases").json()
        if c["id"] == case["id"]
    )
    assert reopened["treated"] is False
    assert client.delete(f"/treatment-cases/{created['id']}").status_code == 404


def test_treated_planned_case_cannot_be_deleted(client):
    case = _first_planned_case(client)
    client.post(
        "/treatment-cases",
        json={
            "student_id": STUDENT,
            "class_id": case["class_id"],
            "patient_case_id": case["id"],
            "semester": "2026SoSe",
        },
    )
    response = client.delete(f"/patients/{PATIENT}/cases/{case['id']}")
    assert response.status_code == 409  # kein 500 durch den Fremdschlüssel


# ------------------------------- Übersicht & Schutz -------------------------------


def test_student_overview(client):
    overview = client.get(f"/students/{STUDENT}/overview")
    assert overview.status_code == 200
    body = overview.json()
    assert body["student"]["id"] == STUDENT
    assert body["categories_done"] + body["categories_open"] == len(
        body["category_progress"]
    )
    assert body["classes_done"] + body["classes_open"] > 0
    assert client.get("/students/9999/overview").status_code == 404


def test_unknown_patient_progress_is_404(client):
    assert client.get("/patients/9999/treatment-progress").status_code == 404


def test_write_endpoints_require_key_when_configured(client, monkeypatch):
    monkeypatch.setenv("PROJEKT2_API_KEY", "geheim")
    category_id = client.get("/categories").json()[0]["id"]
    body = {"student_id": STUDENT, "semester": "2026SoSe", "points": 1}
    url = f"/categories/{category_id}/points"
    assert client.put(url, json=body).status_code == 401
    assert (
        client.put(url, json=body, headers={"X-API-Key": "geheim"}).status_code == 200
    )
    assert client.get("/categories").status_code == 200  # Lesen bleibt offen
