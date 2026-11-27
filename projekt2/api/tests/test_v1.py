"""Tests für Auth/Rollen, Fehlerformat, Pagination, Soft Delete, Audit-Log,
Zuordnungs-Historie, asynchrone Jobs und die versionierten Pfade."""

V1 = "/api/v1"
SECRET = "x" * 40


def _make_user(db, username, role, student_id=None, password="passwort-12345"):
    from app.repositories import users

    users.create_user(db, username, password, role, student_id)
    db.commit()


def _login(client, username, password="passwort-12345"):
    response = client.post(
        f"{V1}/auth/login", json={"username": username, "password": password}
    )
    assert response.status_code == 200, response.json()
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _secured(client, db_session, monkeypatch):
    """JWT-Modus mit je einem Admin, Lehrenden und Studierenden (student_id 0)."""
    monkeypatch.setenv("PROJEKT2_JWT_SECRET", SECRET)
    _make_user(db_session, "admin", "admin")
    _make_user(db_session, "lehrer", "teacher")
    _make_user(db_session, "studi0", "student", student_id=0)
    return {
        "admin": _login(client, "admin"),
        "teacher": _login(client, "lehrer"),
        "student": _login(client, "studi0"),
    }


def _planned_case(client):
    return client.get(f"{V1}/patients/0/cases").json()[0]


def test_v1_and_legacy_paths_both_work(client):
    assert client.get(f"{V1}/health").json() == {"status": "ok"}
    assert client.get(f"{V1}/students").status_code == 200
    assert client.get("/students").status_code == 200


def test_dev_mode_without_secret_is_open_admin(client):
    me = client.get(f"{V1}/me").json()
    assert me["role"] == "admin" and me["auth"] == "dev"


def test_login_503_without_secret(client):
    response = client.post(f"{V1}/auth/login", json={"username": "a", "password": "b"})
    assert response.status_code == 503


def test_requests_need_token_when_secret_is_set(client, db_session, monkeypatch):
    _secured(client, db_session, monkeypatch)
    assert client.get(f"{V1}/students").status_code == 401
    assert client.get("/students").status_code == 401
    assert client.get(f"{V1}/health").status_code == 200
    bad = client.get(f"{V1}/students", headers={"Authorization": "Bearer müll"})
    assert bad.status_code == 401


def test_login_wrong_password_and_unknown_user_look_alike(
    client, db_session, monkeypatch
):
    _secured(client, db_session, monkeypatch)
    wrong = client.post(
        f"{V1}/auth/login", json={"username": "admin", "password": "falsch"}
    )
    unknown = client.post(
        f"{V1}/auth/login", json={"username": "gibtsnicht", "password": "x"}
    )
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"]


def test_login_is_throttled_after_repeated_failures(client, db_session, monkeypatch):
    _secured(client, db_session, monkeypatch)
    for _ in range(5):
        client.post(
            f"{V1}/auth/login", json={"username": "admin", "password": "falsch"}
        )
    blocked = client.post(
        f"{V1}/auth/login", json={"username": "admin", "password": "passwort-12345"}
    )
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers


def test_me_returns_role_and_student_link(client, db_session, monkeypatch):
    tokens = _secured(client, db_session, monkeypatch)
    me = client.get(f"{V1}/me", headers=tokens["student"]).json()
    assert me["role"] == "student" and me["student_id"] == 0 and me["auth"] == "jwt"


def test_student_sees_only_own_data(client, db_session, monkeypatch):
    tokens = _secured(client, db_session, monkeypatch)
    student = tokens["student"]
    own = client.get(f"{V1}/students/0/overview", headers=student)
    assert own.status_code == 200
    assert client.get(f"{V1}/students/1/overview", headers=student).status_code == 403
    assert (
        client.get(f"{V1}/students/1/category-progress", headers=student).status_code
        == 403
    )
    listed = client.get(f"{V1}/students", headers=student).json()
    assert [s["id"] for s in listed] == [0]
    assert (
        client.get(
            f"{V1}/treatment-cases", params={"student_id": 1}, headers=student
        ).status_code
        == 403
    )
    assert client.get(f"{V1}/treatment-cases", headers=student).status_code == 200
    assert (
        client.get(
            f"{V1}/osce/results", params={"student_id": 1}, headers=student
        ).status_code
        == 403
    )
    assert (
        client.get(f"{V1}/students/1/overview", headers=tokens["teacher"]).status_code
        == 200
    )


def test_student_cannot_read_patients_or_write(client, db_session, monkeypatch):
    tokens = _secured(client, db_session, monkeypatch)
    student = tokens["student"]
    assert client.get(f"{V1}/patients", headers=student).status_code == 403
    assert client.get(f"{V1}/assignments", headers=student).status_code == 403
    assert (
        client.get(f"{V1}/analysis/patient-matching", headers=student).status_code
        == 403
    )
    assert client.get(f"{V1}/audit-log", headers=student).status_code == 403
    assert client.get(f"{V1}/users", headers=student).status_code == 403
    body = {"student_id": 0, "class_id": 1, "semester": "2026SoSe"}
    assert (
        client.post(f"{V1}/treatment-cases", json=body, headers=student).status_code
        == 403
    )


def test_teacher_records_treatments_but_does_not_plan(client, db_session, monkeypatch):
    tokens = _secured(client, db_session, monkeypatch)
    teacher = tokens["teacher"]
    case = client.get(f"{V1}/patients/0/cases", headers=teacher).json()[0]
    created = client.post(
        f"{V1}/treatment-cases",
        json={
            "student_id": 0,
            "class_id": case["class_id"],
            "patient_case_id": case["id"],
            "semester": "2026SoSe",
        },
        headers=teacher,
    )
    assert created.status_code == 201
    assert (
        client.patch(
            f"{V1}/classes/1", json={"difficulty": 2}, headers=teacher
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"{V1}/patients", json={"pseudonym": "P-T"}, headers=teacher
        ).status_code
        == 403
    )
    assert (
        client.put(
            f"{V1}/assignments/0", json={"student_id": 0}, headers=teacher
        ).status_code
        == 403
    )
    admin = tokens["admin"]
    assert (
        client.post(
            f"{V1}/patients", json={"pseudonym": "P-T"}, headers=admin
        ).status_code
        == 201
    )


def test_api_key_still_acts_as_service_admin(client, db_session, monkeypatch):
    _secured(client, db_session, monkeypatch)
    monkeypatch.setenv("PROJEKT2_API_KEY", "geheim")
    ok = client.get(f"{V1}/students", headers={"X-API-Key": "geheim"})
    assert ok.status_code == 200
    assert (
        client.get(f"{V1}/students", headers={"X-API-Key": "falsch"}).status_code == 401
    )


def test_production_without_secret_is_rejected_and_fails_closed(client, monkeypatch):
    from app import config

    monkeypatch.setenv("PROJEKT2_ENV", "production")
    assert config.validate_startup_config()
    assert client.get(f"{V1}/students").status_code == 401


def test_user_management_rules(client, db_session, monkeypatch):
    tokens = _secured(client, db_session, monkeypatch)
    admin = tokens["admin"]
    created = client.post(
        f"{V1}/users",
        json={
            "username": "neu",
            "password": "langes-passwort",
            "role": "student",
            "student_id": 1,
        },
        headers=admin,
    )
    assert created.status_code == 201 and "password" not in str(created.json())
    dup = client.post(
        f"{V1}/users",
        json={"username": "neu", "password": "langes-passwort", "role": "teacher"},
        headers=admin,
    )
    assert dup.status_code == 409
    no_link = client.post(
        f"{V1}/users",
        json={"username": "x1x", "password": "langes-passwort", "role": "student"},
        headers=admin,
    )
    assert no_link.status_code == 422
    short = client.post(
        f"{V1}/users",
        json={"username": "x2x", "password": "kurz", "role": "teacher"},
        headers=admin,
    )
    assert short.status_code == 422
    new_id = created.json()["id"]
    token = _login(client, "neu", "langes-passwort")
    assert client.get(f"{V1}/me", headers=token).status_code == 200
    assert (
        client.patch(
            f"{V1}/users/{new_id}", json={"active": False}, headers=admin
        ).status_code
        == 200
    )
    assert client.get(f"{V1}/me", headers=token).status_code == 401
    my_id = client.get(f"{V1}/me", headers=admin).json()["id"]
    assert (
        client.patch(
            f"{V1}/users/{my_id}", json={"active": False}, headers=admin
        ).status_code
        == 409
    )


def test_error_format_is_uniform(client):
    not_found = client.get(f"{V1}/patients/9999")
    body = not_found.json()
    assert not_found.status_code == 404
    assert body["type"] == "not_found" and body["status"] == 404
    assert isinstance(body["detail"], str) and "title" in body

    invalid = client.put(
        f"{V1}/students/0/categories/1/points/2026",
        json={"points": 1},
    )
    assert invalid.status_code == 422 and invalid.json()["type"] == "validation_error"

    missing_body = client.post(f"{V1}/treatment-cases", json={"student_id": 0})
    assert missing_body.status_code == 422
    assert missing_body.json()["errors"]

    assert client.get("/gibt-es-nicht").json()["type"] == "not_found"


def test_pagination_header_and_slicing(client):
    everything = client.get(f"{V1}/patients")
    total = int(everything.headers["X-Total-Count"])
    assert total == len(everything.json()) > 1
    first = client.get(f"{V1}/patients", params={"limit": 1, "offset": 0})
    second = client.get(f"{V1}/patients", params={"limit": 1, "offset": 1})
    assert len(first.json()) == len(second.json()) == 1
    assert first.json()[0]["id"] != second.json()[0]["id"]
    assert first.headers["X-Total-Count"] == str(total)
    assert client.get(f"{V1}/patients", params={"limit": 0}).status_code == 422
    assert client.get(f"{V1}/patients", params={"limit": 501}).status_code == 422
    assert client.get(f"{V1}/patients", params={"offset": -1}).status_code == 422


def test_patient_search_and_sort(client):
    patients = client.get(f"{V1}/patients").json()
    target = patients[0]
    needle = (target["pseudonym"] or target["name"])[:3]
    hits = client.get(f"{V1}/patients", params={"search": needle.lower()}).json()
    assert target["id"] in {p["id"] for p in hits}
    desc = client.get(f"{V1}/patients", params={"sort": "id", "order": "desc"}).json()
    assert [p["id"] for p in desc] == sorted((p["id"] for p in patients), reverse=True)
    assert (
        client.get(f"{V1}/patients", params={"sort": "name; drop table x"}).status_code
        == 422
    )


def test_treatment_case_filters_and_sorting(client):
    case = _planned_case(client)
    for date, semester in (("2026-05-01", "2026SoSe"), ("2026-11-01", "2026WiSe")):
        client.post(
            f"{V1}/treatment-cases",
            json={
                "student_id": 0,
                "class_id": case["class_id"],
                "semester": semester,
                "treatment_date": date,
            },
        )
    in_may = client.get(
        f"{V1}/treatment-cases",
        params={"date_from": "2026-05-01", "date_to": "2026-06-01"},
    ).json()
    assert [c["treatment_date"] for c in in_may] == ["2026-05-01"]
    newest = client.get(
        f"{V1}/treatment-cases", params={"sort": "treatment_date", "order": "desc"}
    ).json()
    assert newest[0]["treatment_date"] == "2026-11-01"
    assert (
        client.get(f"{V1}/treatment-cases", params={"semester": "2026"}).status_code
        == 422
    )


def test_category_points_new_resource_url(client):
    category = client.get(f"{V1}/categories").json()[0]
    url = f"{V1}/students/0/categories/{category['id']}/points/2026SoSe"
    assert client.put(url, json={"points": 5}).status_code == 200
    assert client.put(url, json={"points": 9}).json()["points"] == 9
    direct = client.get(f"{V1}/students/0/category-points").json()
    assert [r["points"] for r in direct if r["category_id"] == category["id"]] == [9]
    progress = next(
        r
        for r in client.get(f"{V1}/students/0/category-progress").json()
        if r["category"] == category["name"]
    )
    assert progress["direct_points"] == 9
    assert (
        progress["total_points"] == progress["class_points"] + progress["direct_points"]
    )
    assert client.delete(url).status_code == 204
    assert client.delete(url).status_code == 404
    assert (
        client.put(
            f"{V1}/students/9999/categories/{category['id']}/points/2026SoSe",
            json={"points": 1},
        ).status_code
        == 404
    )
    assert (
        client.put(
            f"{V1}/students/0/categories/9999/points/2026SoSe", json={"points": 1}
        ).status_code
        == 404
    )


def test_old_category_points_routes_not_in_v1(client):
    category_id = client.get(f"{V1}/categories").json()[0]["id"]
    body = {"student_id": 0, "semester": "2026SoSe", "points": 1}
    assert (
        client.put(f"{V1}/categories/{category_id}/points", json=body).status_code
        == 405
    )
    assert client.put(f"/categories/{category_id}/points", json=body).status_code == 200


def _create_treatment(client, case, **extra):
    response = client.post(
        f"{V1}/treatment-cases",
        json={
            "student_id": 0,
            "class_id": case["class_id"],
            "patient_case_id": case["id"],
            "semester": "2026SoSe",
            **extra,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_delete_is_soft_and_audited(client, db_session):
    from sqlalchemy import text

    case = _planned_case(client)
    created = _create_treatment(client, case)
    url = f"{V1}/treatment-cases/{created['id']}"
    assert client.delete(url, params={"reason": "Fehleingabe"}).status_code == 204
    assert client.get(url).status_code == 404
    assert client.patch(url, json={"notes": "x"}).status_code == 404
    assert created["id"] not in [
        c["id"] for c in client.get(f"{V1}/treatment-cases").json()
    ]
    row = (
        db_session.execute(
            text(
                "select deleted_at, deleted_by, deletion_reason from treatment_cases where id = :id"
            ),
            {"id": created["id"]},
        )
        .mappings()
        .first()
    )
    assert row["deleted_at"] is not None and row["deletion_reason"] == "Fehleingabe"
    reopened = next(
        c for c in client.get(f"{V1}/patients/0/cases").json() if c["id"] == case["id"]
    )
    assert reopened["treated"] is False
    assert (
        client.get(f"{V1}/patients/0/treatment-progress").json()["treated_cases"] == 0
    )
    assert case["id"] in [
        c["id"] for c in client.get(f"{V1}/patients/open-cases").json()
    ]
    assert client.delete(f"{V1}/patients/0/cases/{case['id']}").status_code == 204
    log = client.get(
        f"{V1}/audit-log",
        params={"entity": "treatment_case", "entity_id": str(created["id"])},
    ).json()
    assert [e["action"] for e in log] == ["delete", "create"]
    assert log[0]["reason"] == "Fehleingabe" and log[0]["before"]["student_id"] == 0


def test_patient_with_soft_deleted_treatment_cannot_be_deleted(client):
    created = _create_treatment(client, _planned_case(client))
    client.delete(f"{V1}/treatment-cases/{created['id']}")
    assert client.delete(f"{V1}/patients/0").status_code == 409


def test_patch_is_audited_with_before_and_after(client):
    created = _create_treatment(client, _planned_case(client), notes="alt")
    client.patch(f"{V1}/treatment-cases/{created['id']}", json={"notes": "neu"})
    log = client.get(
        f"{V1}/audit-log", params={"entity": "treatment_case", "action": "update"}
    ).json()
    assert log[0]["before"]["notes"] == "alt" and log[0]["after"]["notes"] == "neu"
    assert log[0]["username"] == "dev"


def test_audit_log_filters_and_other_entities(client):
    client.patch(f"{V1}/classes/1", json={"difficulty": 3})
    client.post(f"{V1}/patients", json={"pseudonym": "P-AUDIT"})
    entities = {e["entity"] for e in client.get(f"{V1}/audit-log").json()}
    assert {"class", "patient"} <= entities
    only = client.get(f"{V1}/audit-log", params={"entity": "class"}).json()
    assert all(e["entity"] == "class" for e in only)
    assert (
        client.get(f"{V1}/audit-log", params={"action": "explode"}).status_code == 422
    )


def test_assignment_replace_keeps_created_at_and_records_history(client):
    first = client.put(
        f"{V1}/assignments/0", json={"student_id": 0, "note": "erst"}
    ).json()
    assert first["updated_at"] == first["created_at"]
    second = client.put(
        f"{V1}/assignments/0", json={"student_id": 1, "note": "zweit"}
    ).json()
    assert second["student_id"] == 1
    assert second["created_at"] == first["created_at"]
    history = client.get(f"{V1}/assignments/0/history").json()
    assert [(h["student_id"], h["note"], h["change"]) for h in history] == [
        (0, "erst", "replaced")
    ]
    assert client.delete(f"{V1}/assignments/0").status_code == 204
    history = client.get(f"{V1}/assignments/0/history").json()
    assert [h["change"] for h in history] == ["replaced", "removed"]
    assert history[-1]["student_id"] == 1
    assert client.get(f"{V1}/assignments/9999/history").status_code == 404
    assert client.get(f"{V1}/assignments").json() == []


def test_async_job_contract(client):
    created = client.post(f"{V1}/analysis/jobs", json={"student_id": 0})
    assert created.status_code == 202
    body = created.json()
    assert body["status"] == "queued" and body["job_id"]
    job = client.get(f"{V1}/analysis/jobs/{body['job_id']}").json()
    assert job["status"] == "completed" and job["progress"] == 1
    assert job["result"]["student_id"] == 0 and job["result"]["source"] == "placeholder"
    assert job["finished_at"] is not None
    assert client.get(f"{V1}/analysis/jobs/gibtsnicht").status_code == 404
    assert (
        client.post(f"{V1}/analysis/jobs", json={"student_id": 9999}).status_code == 404
    )


def test_legacy_trigger_still_works_and_is_persistent(client, db_session):
    from sqlalchemy import text

    response = client.post("/analysis/students/0/trigger")
    assert response.status_code == 200 and response.json()["status"] == "completed"
    job_id = response.json()["job_id"]
    assert client.get(f"/analysis/jobs/{job_id}").json()["status"] == "completed"
    count = db_session.execute(text("select count(*) from analysis_jobs")).scalar()
    assert count == 1


def test_failed_job_is_recorded(client, monkeypatch):
    from app.routers import analysis

    def boom(_trajectory):
        raise RuntimeError("LLM nicht erreichbar")

    monkeypatch_target = analysis
    original = monkeypatch_target.call_llm_for_insights
    monkeypatch_target.call_llm_for_insights = boom
    try:
        job_id = client.post(f"{V1}/analysis/jobs", json={"student_id": 0}).json()[
            "job_id"
        ]
    finally:
        monkeypatch_target.call_llm_for_insights = original
    job = client.get(f"{V1}/analysis/jobs/{job_id}").json()
    assert job["status"] == "failed" and "nicht erreichbar" in job["error"]


def test_orphaned_jobs_are_failed_on_startup(client, db_session):
    from sqlalchemy import text

    from app.repositories import jobs

    job_id = jobs.create(db_session, 0, "test")
    db_session.commit()
    assert jobs.fail_orphans(db_session) == 1
    db_session.commit()
    row = db_session.execute(
        text("select status from analysis_jobs where id = :id"), {"id": job_id}
    ).scalar()
    assert row == "failed"


def test_student_can_read_only_own_job(client, db_session, monkeypatch):
    tokens = _secured(client, db_session, monkeypatch)
    mine = client.post(
        f"{V1}/analysis/jobs", json={"student_id": 0}, headers=tokens["teacher"]
    ).json()["job_id"]
    other = client.post(
        f"{V1}/analysis/jobs", json={"student_id": 1}, headers=tokens["teacher"]
    ).json()["job_id"]
    assert (
        client.get(f"{V1}/analysis/jobs/{mine}", headers=tokens["student"]).status_code
        == 200
    )
    assert (
        client.get(f"{V1}/analysis/jobs/{other}", headers=tokens["student"]).status_code
        == 403
    )
    assert (
        client.post(
            f"{V1}/analysis/jobs", json={"student_id": 0}, headers=tokens["student"]
        ).status_code
        == 403
    )


def test_matching_reports_algorithm_version_and_explanations(client):
    matching = client.get(f"{V1}/analysis/patient-matching").json()
    assert matching["strategy"] == "hungarian"
    assert matching["algorithm_version"] == "class-match-v2"
    for assignment in matching["assignments"]:
        assert assignment["algorithm_version"] == "class-match-v2"
        assert assignment["round"] >= 1
        for explained in assignment["matched_classes"]:
            assert (
                "deficit_points_before" in explained and "covered_points" in explained
            )
    recs = client.get(f"{V1}/analysis/students/0/patient-recommendations").json()
    assert all(r["algorithm_version"] == "class-match-v1" for r in recs)


def _used_patients(matching):
    return [a["patient_id"] for a in matching["assignments"]]


def test_hungarian_matching_is_consistent(client):
    patients = {p["id"] for p in client.get(f"{V1}/patients").json()}
    matching = client.get(f"{V1}/analysis/patient-matching").json()
    used = _used_patients(matching)
    unmatched = [u["patient_id"] for u in matching["unmatched_patients"]]
    assert len(used) == len(set(used))
    assert set(used) | set(unmatched) <= patients
    assert not set(used) & set(unmatched)
    assert matching["total_score"] == round(
        sum(a["score"] for a in matching["assignments"]), 2
    )
    by_round = {}
    for a in matching["assignments"]:
        by_round.setdefault(a["round"], []).append(a["student_id"])
    for students in by_round.values():
        assert len(students) == len(set(students))


def test_hungarian_is_never_worse_than_greedy_in_round_one(client):
    hungarian = client.get(f"{V1}/analysis/patient-matching").json()
    greedy = client.get(
        f"{V1}/analysis/patient-matching", params={"strategy": "greedy"}
    ).json()
    assert (
        greedy["strategy"] == "greedy"
        and greedy["algorithm_version"] == "class-match-v1"
    )
    first = sum(a["score"] for a in hungarian["assignments"] if a["round"] == 1)
    greedy_first_round = {}
    for a in greedy["assignments"]:
        greedy_first_round.setdefault(a["student_id"], a["score"])
    firsts, seen = 0.0, set()
    for a in greedy["assignments"]:
        if a["student_id"] not in seen:
            seen.add(a["student_id"])
            firsts += a["score"]
    assert first + 1e-9 >= firsts


def test_max_per_student_limits_assignments(client):
    for strategy in ("hungarian", "greedy"):
        matching = client.get(
            f"{V1}/analysis/patient-matching",
            params={"strategy": strategy, "max_per_student": 1},
        ).json()
        students = [a["student_id"] for a in matching["assignments"]]
        assert len(students) == len(set(students))
    assert (
        client.get(
            f"{V1}/analysis/patient-matching", params={"max_per_student": 0}
        ).status_code
        == 422
    )
    assert (
        client.get(
            f"{V1}/analysis/patient-matching", params={"strategy": "zufall"}
        ).status_code
        == 422
    )
