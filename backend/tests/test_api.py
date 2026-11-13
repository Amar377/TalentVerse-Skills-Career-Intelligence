"""Comprehensive automated test suite for TalentVerse 2.0 API."""
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import (
    SessionLocal,
    User,
    CandidateProfileModel,
    ResumeRecordModel,
    RoadmapModel,
    JobMatchModel,
    ProjectBriefModel,
    InterviewModel,
    SavedReportModel,
)
from backend.schemas import CandidateProfileData
from backend.auth_utils import hash_password, verify_password
from datetime import datetime, timedelta
import os
import pytest
import threading
from uuid import uuid4

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_frontend_static_route_does_not_serve_files_outside_dist():
    response = client.get("/%2e%2e/.env")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_system_status():
    res = client.get("/api/v1/system/status")
    assert res.status_code == 200
    data = res.json()
    assert "priority" in data
    assert "providers" in data
    assert len(data["providers"]) > 0


def test_demo_login_and_auth():
    res = client.post("/api/v1/auth/demo")
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"].startswith("demo-session-")
    assert data["user"]["is_demo"] is True

    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["id"] == data["user"]["id"]


def test_demo_sessions_isolate_user_owned_data():
    first = client.post("/api/v1/auth/demo")
    second = client.post("/api/v1/auth/demo")
    assert first.status_code == second.status_code == 200
    first_data = first.json()
    second_data = second.json()
    assert first_data["user"]["id"] != second_data["user"]["id"]

    first_headers = {"Authorization": f"Bearer {first_data['access_token']}"}
    second_headers = {"Authorization": f"Bearer {second_data['access_token']}"}
    for headers, expected_id in (
        (first_headers, first_data["user"]["id"]),
        (second_headers, second_data["user"]["id"]),
    ):
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["id"] == expected_id

    db = SessionLocal()
    first_report = SavedReportModel(
        user_id=first_data["user"]["id"],
        report_type="resume",
        title="Private first demo report",
        data={"private": "first demo workspace"},
    )
    report = SavedReportModel(
        user_id=second_data["user"]["id"],
        report_type="resume",
        title="Private demo report",
        data={"private": "second demo workspace"},
    )
    first_resume = ResumeRecordModel(
        user_id=first_data["user"]["id"],
        filename="first-private-resume.txt",
        file_type="text",
        raw_text="Private resume text belonging only to demo session one.",
        parsed_profile=CandidateProfileData(full_name="First Demo Candidate").model_dump(),
    )
    resume = ResumeRecordModel(
        user_id=second_data["user"]["id"],
        filename="private-resume.txt",
        file_type="text",
        raw_text="Private resume text belonging only to demo session two.",
        parsed_profile=CandidateProfileData(full_name="Private Demo Candidate").model_dump(),
    )
    roadmap = RoadmapModel(
        user_id=second_data["user"]["id"],
        career_goal="Private demo roadmap",
        milestones=[
            {
                "week": 1,
                "title": "Private milestone",
                "learning_tasks": [],
                "deliverable": "Private deliverable",
                "success_criteria": [],
                "completed": False,
            }
        ],
    )
    normal_user = User(
        email=f"normal-isolation-{uuid4().hex}@example.com",
        hashed_password="unused",
    )
    db.add(normal_user)
    db.flush()
    normal_profile = CandidateProfileModel(user_id=normal_user.id)
    normal_report = SavedReportModel(
        user_id=normal_user.id,
        report_type="resume",
        title="Private registered-user report",
        data={"private": "registered-user workspace"},
    )
    db.add_all(
        [first_report, report, first_resume, resume, roadmap, normal_profile, normal_report]
    )
    db.flush()
    db.commit()
    first_report_id = first_report.id
    report_id = report.id
    first_resume_text = first_resume.raw_text
    resume_text = resume.raw_text
    roadmap_id = roadmap.id
    normal_profile_id = normal_profile.id
    normal_report_id = normal_report.id
    normal_user_id = normal_user.id
    first_profile_id = (
        db.query(CandidateProfileModel.id)
        .filter_by(user_id=first_data["user"]["id"])
        .scalar()
    )
    second_profile_id = (
        db.query(CandidateProfileModel.id)
        .filter_by(user_id=second_data["user"]["id"])
        .scalar()
    )
    db.close()

    assert first_profile_id != second_profile_id
    assert [
        item["id"] for item in client.get("/api/v1/reports", headers=first_headers).json()
    ] == [first_report_id]
    assert [
        item["id"] for item in client.get("/api/v1/reports", headers=second_headers).json()
    ] == [report_id]
    assert client.get(f"/api/v1/reports/{report_id}", headers=first_headers).status_code == 404
    assert client.delete(f"/api/v1/reports/{report_id}", headers=first_headers).status_code == 404
    assert client.get(f"/api/v1/reports/{first_report_id}", headers=second_headers).status_code == 404
    assert client.delete(f"/api/v1/reports/{first_report_id}", headers=second_headers).status_code == 404
    assert client.get(f"/api/v1/reports/{report_id}", headers=second_headers).status_code == 200

    first_resume_result = client.get("/api/v1/resumes/latest", headers=first_headers)
    assert first_resume_result.status_code == 200
    assert first_resume_result.json()["raw_text"] == first_resume_text
    second_resume = client.get("/api/v1/resumes/latest", headers=second_headers)
    assert second_resume.status_code == 200
    assert second_resume.json()["raw_text"] == resume_text
    assert second_resume.json()["raw_text"] != first_resume_text

    first_profile_access = client.post(
        "/api/v1/jobs/match",
        json={
            "profile_id": second_profile_id,
            "job_description": "A sufficiently detailed job description for profile ownership testing.",
        },
        headers=first_headers,
    )
    second_profile_access = client.post(
        "/api/v1/jobs/match",
        json={
            "profile_id": first_profile_id,
            "job_description": "A sufficiently detailed job description for profile ownership testing.",
        },
        headers=second_headers,
    )
    assert first_profile_access.status_code == second_profile_access.status_code == 404

    from backend.auth_utils import create_access_token
    normal_headers = {
        "Authorization": f"Bearer {create_access_token({'sub': normal_user_id})}"
    }
    assert client.get(f"/api/v1/reports/{normal_report_id}", headers=normal_headers).status_code == 200
    assert client.get(f"/api/v1/reports/{normal_report_id}", headers=first_headers).status_code == 404
    assert client.delete(f"/api/v1/reports/{normal_report_id}", headers=second_headers).status_code == 404
    assert client.get(f"/api/v1/reports/{report_id}", headers=normal_headers).status_code == 404
    normal_profile_access = client.post(
        "/api/v1/jobs/match",
        json={
            "profile_id": first_profile_id,
            "job_description": "A sufficiently detailed job description for profile ownership testing.",
        },
        headers=normal_headers,
    )
    assert normal_profile_access.status_code == 404

    update_roadmap = client.put(
        f"/api/v1/roadmaps/{roadmap_id}/milestone",
        json={"week": 1, "completed": True},
        headers=first_headers,
    )
    assert update_roadmap.status_code == 404
    db = SessionLocal()
    stored_roadmap = db.query(RoadmapModel).filter_by(id=roadmap_id).first()
    assert stored_roadmap.milestones[0]["completed"] is False
    assert db.query(SavedReportModel).filter_by(id=report_id).first() is not None
    assert db.query(SavedReportModel).filter_by(id=first_report_id).first() is not None
    assert db.query(SavedReportModel).filter_by(id=normal_report_id).first() is not None
    assert db.query(User).filter_by(id=normal_user_id).first() is not None
    db.close()


def test_registered_user_can_still_register_and_login():
    email = f"normal-{uuid4().hex}@example.com"
    password = "ordinary-account-password"
    registration = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Normal User"},
    )
    assert registration.status_code == 200
    user_id = registration.json()["user"]["id"]
    assert registration.json()["user"]["is_demo"] is False

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    assert login.json()["user"]["id"] == user_id


def test_expired_demo_session_cleanup_preserves_legacy_demo_account():
    demo = client.post("/api/v1/auth/demo").json()
    expired_at = datetime.utcnow() - timedelta(days=8)
    db = SessionLocal()
    demo_user = db.query(User).filter_by(id=demo["user"]["id"]).one()
    demo_user.created_at = expired_at
    demo_profile_id = (
        db.query(CandidateProfileModel.id)
        .filter_by(user_id=demo_user.id)
        .scalar()
    )
    report = SavedReportModel(
        user_id=demo_user.id,
        report_type="resume",
        title="Expired demo report",
        data={"private": "expired demo data"},
    )
    resume = ResumeRecordModel(
        user_id=demo_user.id,
        filename="expired-resume.txt",
        file_type="text",
        raw_text="Expired demo resume text that should be cleaned up.",
        parsed_profile=CandidateProfileData(full_name="Expired Demo Candidate").model_dump(),
    )
    roadmap = RoadmapModel(user_id=demo_user.id, career_goal="Expired demo goal")
    job_match = JobMatchModel(
        user_id=demo_user.id,
        target_role="Expired demo role",
        job_description="Expired demo job description",
    )
    project = ProjectBriefModel(
        user_id=demo_user.id,
        title="Expired demo project",
        problem_statement="Expired demo problem",
    )
    interview = InterviewModel(
        user_id=demo_user.id,
        target_role="Expired demo role",
        question="Expired demo question",
    )

    normal_user = User(
        email=f"normal-cleanup-{uuid4().hex}@example.com",
        hashed_password="unused",
    )
    db.add(normal_user)
    db.flush()
    normal_profile = CandidateProfileModel(user_id=normal_user.id)
    normal_resume = ResumeRecordModel(user_id=normal_user.id, raw_text="Normal user resume")
    normal_roadmap = RoadmapModel(user_id=normal_user.id, career_goal="Normal user goal")
    normal_job_match = JobMatchModel(
        user_id=normal_user.id,
        target_role="Normal user role",
        job_description="Normal user job description",
    )
    normal_project = ProjectBriefModel(
        user_id=normal_user.id,
        title="Normal user project",
        problem_statement="Normal user problem",
    )
    normal_interview = InterviewModel(
        user_id=normal_user.id,
        target_role="Normal user role",
        question="Normal user question",
    )
    normal_report = SavedReportModel(
        user_id=normal_user.id,
        report_type="resume",
        title="Normal user report",
        data={"private": "normal user data"},
    )
    db.add_all(
        [
            report,
            resume,
            roadmap,
            job_match,
            project,
            interview,
            normal_profile,
            normal_resume,
            normal_roadmap,
            normal_job_match,
            normal_project,
            normal_interview,
            normal_report,
        ]
    )
    db.flush()
    demo_ids = {
        model: db.query(model.id).filter_by(user_id=demo_user.id).all()
        for model in (
            CandidateProfileModel,
            ResumeRecordModel,
            RoadmapModel,
            JobMatchModel,
            ProjectBriefModel,
            InterviewModel,
            SavedReportModel,
        )
    }
    normal_user_id = normal_user.id

    legacy_user = db.query(User).filter_by(email="demo@talentverse.ai").first()
    legacy_password = uuid4().hex
    if not legacy_user:
        legacy_user = User(
            email="demo@talentverse.ai",
            hashed_password=hash_password(legacy_password),
            full_name="Legacy Demo",
            is_demo=True,
            created_at=expired_at,
        )
        db.add(legacy_user)
        db.flush()
    legacy_user_id = legacy_user.id
    legacy_report = SavedReportModel(
        user_id=legacy_user_id,
        report_type="resume",
        title="Legacy demo report",
        data={"private": "preserved legacy data"},
    )
    db.add(legacy_report)
    db.flush()
    legacy_report_id = legacy_report.id
    legacy_profile = CandidateProfileModel(user_id=legacy_user_id, full_name="Legacy profile")
    db.add(legacy_profile)
    db.flush()
    legacy_profile_id = legacy_profile.id
    db.commit()
    db.close()

    from backend.auth_utils import create_access_token
    assert client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {create_access_token({'sub': legacy_user_id})}"},
    ).status_code == 401
    assert client.post(
        "/api/v1/auth/login",
        json={"email": "demo@talentverse.ai", "password": legacy_password},
    ).status_code == 401

    from backend.routes.auth import cleanup_expired_demo_sessions

    db = SessionLocal()
    cleanup_expired_demo_sessions(db)
    db.commit()
    db.close()

    old_session = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {demo['access_token']}"},
    )
    assert old_session.status_code == 401

    db = SessionLocal()
    assert db.query(User).filter_by(id=demo["user"]["id"]).first() is None
    for model, record_ids in demo_ids.items():
        assert all(
            db.query(model).filter_by(id=record_id[0]).first() is None
            for record_id in record_ids
        )
        assert db.query(model).filter_by(user_id=normal_user_id).count() == 1
    assert db.query(User).filter_by(id=legacy_user_id).first() is not None
    assert db.query(SavedReportModel).filter_by(id=legacy_report_id).first() is not None
    assert db.query(CandidateProfileModel).filter_by(id=legacy_profile_id).first() is not None
    db.close()


def test_expired_demo_jwt_is_rejected_while_user_still_exists():
    from backend.auth_utils import create_access_token

    demo = client.post("/api/v1/auth/demo").json()
    expired_token = create_access_token(
        {"sub": demo["user"]["id"]},
        expires_delta=timedelta(seconds=-1),
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401

    db = SessionLocal()
    assert db.query(User).filter_by(id=demo["user"]["id"]).first() is not None
    db.close()


def test_expired_demo_session_is_cleaned_without_a_new_demo_login(monkeypatch):
    import backend.main as main

    cleanup_finished = threading.Event()
    cleanup_invocations = []
    original_cleanup = main._cleanup_expired_demo_sessions_once

    def cleanup_and_signal():
        cleanup_invocations.append(True)
        original_cleanup()
        cleanup_finished.set()

    monkeypatch.setattr(main, "_cleanup_expired_demo_sessions_once", cleanup_and_signal)
    demo = client.post("/api/v1/auth/demo").json()
    db = SessionLocal()
    demo_user = db.query(User).filter_by(id=demo["user"]["id"]).one()
    demo_user.created_at = datetime.utcnow() - timedelta(days=8)
    db.add(
        SavedReportModel(
            user_id=demo_user.id,
            report_type="resume",
            title="Scheduled cleanup report",
            data={"private": "expired demo data"},
        )
    )
    db.commit()
    demo_user_id = demo_user.id
    db.close()

    with TestClient(app):
        assert cleanup_finished.wait(timeout=5)

    assert len(cleanup_invocations) == 1
    db = SessionLocal()
    assert db.query(User).filter_by(id=demo_user_id).first() is None
    assert db.query(SavedReportModel).filter_by(user_id=demo_user_id).count() == 0
    db.close()


def test_cleanup_worker_waits_for_inflight_database_work_on_shutdown(monkeypatch):
    import asyncio
    import backend.main as main

    cleanup_started = threading.Event()
    allow_cleanup_to_finish = threading.Event()
    cleanup_finished = threading.Event()

    def blocking_cleanup():
        cleanup_started.set()
        allow_cleanup_to_finish.wait(timeout=5)
        cleanup_finished.set()

    monkeypatch.setattr(main, "_cleanup_expired_demo_sessions_once", blocking_cleanup)

    async def exercise_lifespan_shutdown():
        lifespan_context = main.lifespan(app)
        await lifespan_context.__aenter__()
        assert await asyncio.to_thread(cleanup_started.wait, 5)
        shutdown_task = asyncio.create_task(
            lifespan_context.__aexit__(None, None, None)
        )
        try:
            await asyncio.sleep(0)
            assert not shutdown_task.done()
        finally:
            allow_cleanup_to_finish.set()
        await asyncio.wait_for(shutdown_task, timeout=5)
        assert cleanup_finished.is_set()

    asyncio.run(exercise_lifespan_shutdown())


def test_protected_routes_reject_missing_and_invalid_tokens():
    assert client.get("/api/v1/profiles/me").status_code == 401
    assert client.get(
        "/api/v1/profiles/me",
        headers={"Authorization": "Bearer invalid-token"},
    ).status_code == 401


@pytest.mark.parametrize(
    "payload",
    [{}, {"sub": None}, {"sub": ""}, {"sub": 42}, {"sub": []}, {"sub": {}}],
)
def test_non_string_or_missing_jwt_subject_is_rejected(monkeypatch, payload):
    import backend.auth_utils as auth_utils
    from backend.auth_utils import create_access_token

    token = create_access_token({"sub": "test-subject"})
    monkeypatch.setattr(
        auth_utils.jwt,
        "decode",
        lambda *_args, **_kwargs: payload,
    )
    response = client.get(
        "/api/v1/profiles/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_expired_demo_cleanup_rolls_back_all_deletes_on_database_error():
    from sqlalchemy import text
    import backend.main as main

    engine = SessionLocal.kw["bind"]
    if engine.dialect.name != "sqlite":
        pytest.skip("This rollback regression uses a SQLite delete trigger.")

    demo = client.post("/api/v1/auth/demo").json()
    db = SessionLocal()
    demo_user = db.query(User).filter_by(id=demo["user"]["id"]).one()
    demo_user.created_at = datetime.utcnow() - timedelta(days=8)
    profile = db.query(CandidateProfileModel).filter_by(user_id=demo_user.id).one()
    resume = ResumeRecordModel(
        user_id=demo_user.id,
        raw_text="Resume preserved if cleanup transaction rolls back.",
    )
    report = SavedReportModel(
        user_id=demo_user.id,
        report_type="resume",
        title="Report preserved if cleanup transaction rolls back",
        data={"private": "rollback fixture"},
    )
    db.add_all([resume, report])
    db.commit()
    demo_user_id = demo_user.id
    profile_id = profile.id
    resume_id = resume.id
    report_id = report.id

    db.execute(
        text(
            "CREATE TRIGGER fail_demo_report_delete "
            "BEFORE DELETE ON saved_reports "
            "BEGIN SELECT RAISE(ABORT, 'forced cleanup failure'); END"
        )
    )
    db.commit()
    try:
        main._cleanup_expired_demo_sessions_once()
    finally:
        db.execute(text("DROP TRIGGER IF EXISTS fail_demo_report_delete"))
        db.commit()

    assert db.query(User).filter_by(id=demo_user_id).first() is not None
    assert db.query(CandidateProfileModel).filter_by(id=profile_id).first() is not None
    assert db.query(ResumeRecordModel).filter_by(id=resume_id).first() is not None
    assert db.query(SavedReportModel).filter_by(id=report_id).first() is not None
    db.close()


def test_password_hashes_use_independent_salts_and_verify_legacy_hashes():
    first = hash_password("correct horse battery staple")
    second = hash_password("correct horse battery staple")
    assert first != second
    assert verify_password("correct horse battery staple", first)
    assert not verify_password("wrong password", first)

    from backend.config import SECRET_KEY
    import hashlib

    legacy_salt = SECRET_KEY[:16].encode("utf-8")
    legacy_hash = hashlib.pbkdf2_hmac(
        "sha256", b"legacy password", legacy_salt, 100_000
    ).hex()
    assert verify_password("legacy password", legacy_hash)


def test_resume_parser_rejects_unsupported_legacy_doc_format():
    from backend.file_parser import parse_resume_file

    try:
        parse_resume_file("resume.doc", b"not a supported Word document")
    except ValueError as exc:
        assert "Unsupported file format" in str(exc)
    else:
        raise AssertionError("Legacy .doc must not be treated as a .docx file")


def test_candidate_profile():
    token = client.post("/api/v1/auth/demo").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/profiles/me", headers=headers)
    assert res.status_code == 200
    profile = res.json()
    assert "skills" in profile
    assert profile["readiness_score"] >= 0

    # Update profile
    profile["summary"] = "Updated full stack developer summary testing persistence."
    put_res = client.put("/api/v1/profiles/me", json=profile, headers=headers)
    assert put_res.status_code == 200
    assert put_res.json()["summary"] == profile["summary"]


def test_profile_list_is_scoped_to_authenticated_user():
    token = client.post("/api/v1/auth/demo").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    db = SessionLocal()
    other_user = User(email="profile-scope-test@example.com", hashed_password="unused")
    db.add(other_user)
    db.flush()
    other_profile = CandidateProfileModel(user_id=other_user.id, full_name="Private Test Profile")
    db.add(other_profile)
    db.commit()
    other_profile_id = other_profile.id
    other_user_id = other_user.id
    db.close()

    try:
        response = client.get("/api/v1/profiles", headers=headers)
        assert response.status_code == 200
        assert all(profile["id"] != other_profile_id for profile in response.json())
    finally:
        db = SessionLocal()
        db.query(CandidateProfileModel).filter_by(user_id=other_user_id).delete()
        db.query(User).filter_by(id=other_user_id).delete()
        db.commit()
        db.close()


def test_new_profile_does_not_copy_another_users_legacy_data():
    from backend.auth_utils import create_access_token
    from uuid import uuid4

    db = SessionLocal()
    email = f"profile-seed-{uuid4()}@example.com"
    user = User(email=email, hashed_password="unused", full_name="Isolated Candidate")
    db.add(user)
    db.commit()
    user_id = user.id
    db.close()
    headers = {"Authorization": f"Bearer {create_access_token({'sub': user_id})}"}

    response = client.get("/api/v1/profiles/me", headers=headers)
    assert response.status_code == 200
    profile = response.json()
    assert profile["email"] == email
    assert profile["full_name"] == "Isolated Candidate"
    assert profile["skills"] == []
    assert profile["readiness_score"] == 0


def test_ai_unavailable_returns_service_unavailable(monkeypatch):
    import backend.ai_engine as ai_engine

    monkeypatch.setattr(ai_engine, "AI_PROVIDER_ORDER", [])
    token = client.post("/api/v1/auth/demo").json()["access_token"]
    response = client.post(
        "/api/v1/interviews/questions",
        json={"target_role": "Backend Engineer", "interview_type": "technical", "level": "Entry-level"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 503
    assert "AI provider" in response.json()["detail"]


def test_resume_retry_reuses_recent_analysis(monkeypatch):
    import backend.routes.resumes as resumes

    token = client.post("/api/v1/auth/demo").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    user_id = client.get("/api/v1/auth/me", headers=headers).json()["id"]
    raw_text = "A sufficiently detailed candidate resume with Python, React, and API development experience."
    monkeypatch.setattr(
        resumes,
        "analyze_resume_ai",
        lambda text, session_id: (CandidateProfileData(summary="Test analysis summary."), "Test provider", "test-model"),
    )

    db = SessionLocal()
    resumes_before = db.query(ResumeRecordModel).filter_by(user_id=user_id).count()
    reports_before = db.query(SavedReportModel).filter_by(user_id=user_id, report_type="resume").count()
    db.close()

    first = client.post("/api/v1/resumes/analyze-text", json={"resume_text": raw_text}, headers=headers)
    second = client.post("/api/v1/resumes/analyze-text", json={"resume_text": raw_text}, headers=headers)
    assert first.status_code == second.status_code == 200
    assert second.json()["provider_used"] is None
    assert second.json()["model_used"] is None

    db = SessionLocal()
    assert db.query(ResumeRecordModel).filter_by(user_id=user_id).count() == resumes_before + 1
    assert db.query(SavedReportModel).filter_by(user_id=user_id, report_type="resume").count() == reports_before + 1
    db.close()


def test_dashboard_analytics():
    token = client.post("/api/v1/auth/demo").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/analytics/dashboard", headers=headers)
    assert res.status_code == 200
    stats = res.json()
    assert "career_readiness_score" in stats
    assert "skills_distribution" in stats
    assert "recent_activities" in stats
    assert "recommended_actions" in stats


def test_job_matcher():
    if os.getenv("RUN_LIVE_AI_TESTS") != "1":
        pytest.skip("Set RUN_LIVE_AI_TESTS=1 to call a configured external AI provider.")

    from backend.ai_engine import get_configured_providers
    if not get_configured_providers():
        pytest.skip("No AI provider keys are configured for live integration testing.")

    token = client.post("/api/v1/auth/demo").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    job_desc = (
        "Looking for a Full Stack Engineer with strong experience in Python, FastAPI, "
        "React, SQL databases, Docker, and RESTful API architecture. Familiarity with Kubernetes is a plus."
    )
    res = client.post(
        "/api/v1/jobs/match",
        json={
            "job_description": job_desc,
            "target_role": "Full Stack Engineer",
            "company": "NextGen Systems",
        },
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert 0 <= data["match_score_percent"] <= 100
    assert len(data["matching_skills"]) > 0
    assert "missing_or_unverified_skills" in data
    assert "caveat" in data


def test_interview_questions():
    if os.getenv("RUN_LIVE_AI_TESTS") != "1":
        pytest.skip("Set RUN_LIVE_AI_TESTS=1 to call a configured external AI provider.")

    from backend.ai_engine import get_configured_providers
    if not get_configured_providers():
        pytest.skip("No AI provider keys are configured for live integration testing.")

    token = client.post("/api/v1/auth/demo").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/api/v1/interviews/questions",
        json={
            "target_role": "Backend Engineer",
            "interview_type": "technical",
            "level": "Entry-level",
        },
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["questions"]) > 0
    assert "question" in data["questions"][0]


def test_reports_lifecycle():
    token = client.post("/api/v1/auth/demo").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # List reports
    res = client.get("/api/v1/reports", headers=headers)
    assert res.status_code == 200
    reports = res.json()
    assert isinstance(reports, list)
