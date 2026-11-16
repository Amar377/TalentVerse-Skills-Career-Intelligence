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


def _complete_resume_ai_payload():
    payload = CandidateProfileData().model_dump(mode="json")
    payload.update(
        {
            "full_name": "Test Candidate",
            "summary_quality_analysis": "No standalone summary section was found.",
            "summary_improvement_suggestions": ["Add a concise summary using supported experience."],
            "skills": ["SQL"],
            "skills_by_category": {"Data": ["SQL"]},
            "experience": ["Data analyst at Example Co."],
            "experience_analysis": [
                {
                    "company": "Example Co",
                    "job_title": "Data Analyst",
                    "duration": None,
                    "responsibilities": ["Prepared reports."],
                    "achievements": [],
                    "missing_measurable_results": [],
                    "suggestions": [],
                }
            ],
            "education": ["B.S. Statistics"],
            "education_analysis": [
                {
                    "degree": "B.S. Statistics",
                    "institution": "Example University",
                    "graduation_year": "2021",
                }
            ],
            "projects": ["Sales dashboard built with SQL."],
            "projects_analysis": [
                {
                    "name": "Sales dashboard",
                    "technologies": ["SQL"],
                    "description": "Summarized sales trends.",
                    "achievements": [],
                    "suggestions": [],
                }
            ],
            "ats_score": 60,
            "ats_score_explanation": "The resume has relevant skills and needs a standalone summary.",
            "ats_matched_keywords": ["SQL"],
            "ats_missing_keywords": [],
            "ats_formatting_issues": [],
            "ats_section_completeness": {
                "summary": False,
                "skills": True,
                "experience": True,
                "education": True,
                "projects": True,
            },
        }
    )
    return payload


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
    first_resume_profile = _complete_resume_ai_payload()
    first_resume_profile["full_name"] = "First Demo Candidate"
    first_resume_profile["_provided_fields"] = sorted(CandidateProfileData.model_fields)
    second_resume_profile = _complete_resume_ai_payload()
    second_resume_profile["full_name"] = "Private Demo Candidate"
    second_resume_profile["_provided_fields"] = sorted(CandidateProfileData.model_fields)
    first_resume = ResumeRecordModel(
        user_id=first_data["user"]["id"],
        filename="first-private-resume.txt",
        file_type="text",
        raw_text="Private resume text belonging only to demo session one.",
        parsed_profile=first_resume_profile,
    )
    resume = ResumeRecordModel(
        user_id=second_data["user"]["id"],
        filename="private-resume.txt",
        file_type="text",
        raw_text="Private resume text belonging only to demo session two.",
        parsed_profile=second_resume_profile,
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
        assert "PDF, DOCX, TXT, or Markdown (.md)" in str(exc)
    else:
        raise AssertionError("Legacy .doc must not be treated as a .docx file")


def test_resume_upload_supports_every_advertised_file_format(monkeypatch):
    import io
    import pymupdf
    from docx import Document
    import backend.routes.resumes as resumes

    resume_text = (
        "Jane Doe - Software Engineer. Python, FastAPI, and React developer. "
        "Built reliable production web applications and data services."
    )
    docx_buffer = io.BytesIO()
    docx_document = Document()
    docx_document.add_paragraph(resume_text)
    docx_document.save(docx_buffer)

    pdf_document = pymupdf.open()
    pdf_document.new_page().insert_text((72, 72), resume_text)
    pdf_bytes = pdf_document.tobytes()
    pdf_document.close()

    monkeypatch.setattr(
        resumes,
        "analyze_resume_ai",
        lambda text, session_id, preferred_provider=None: (
            CandidateProfileData(full_name="Jane Doe", summary=text[:80]),
            "groq",
            "test-model",
        ),
    )
    token = client.post("/api/v1/auth/demo").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    uploads = [
        ("resume.pdf", pdf_bytes, "application/pdf"),
        (
            "resume.docx",
            docx_buffer.getvalue(),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
        ("resume.txt", (resume_text + " TXT format.").encode(), "text/plain"),
        ("resume.md", ("# Resume\n\n" + resume_text + " Markdown format.").encode(), "text/markdown"),
    ]

    for filename, contents, content_type in uploads:
        response = client.post(
            "/api/v1/resumes/upload",
            files={"file": (filename, contents, content_type)},
            data={"preferred_provider": "groq"},
            headers=headers,
        )
        assert response.status_code == 200, (filename, response.text)
        assert "Jane Doe" in response.json()["raw_text"]
        assert response.json()["provider_used"] == "groq"


def test_resume_upload_returns_ats_sections_and_updates_candidate_profile(monkeypatch):
    import backend.routes.resumes as resumes

    extracted_profile = CandidateProfileData(
        full_name="Resume Candidate",
        target_role="Data Analyst",
        experience_level="Mid-level",
        summary="Data analyst experienced in building SQL reporting and Python data pipelines.",
        skills=["SQL", "Python"],
        experience=["Data Analyst at Example Co: built reporting pipelines."],
        education=["B.S. Statistics"],
        projects=["Sales analysis dashboard built with Python."],
        readiness_score=78,
        current_role="Data Analyst",
        total_experience="3 years",
        summary_quality_analysis="Relevant skills are visible, but the summary could be more concise.",
        summary_improvement_suggestions=["Lead with the strongest evidenced analytics skill."],
        skills_by_category={"Data": ["SQL", "Python"]},
        target_role_skill_alignment=["SQL is evidenced in project and work descriptions."],
        experience_analysis=[
            {
                "company": "Example Co",
                "job_title": "Data Analyst",
                "duration": "2022-2025",
                "responsibilities": ["Built sales reports."],
                "achievements": ["Automated recurring analysis."],
                "missing_measurable_results": ["Add verified time savings if available."],
                "suggestions": ["Quantify the reporting improvement using a verified metric."],
            }
        ],
        education_analysis=[
            {"degree": "B.S. Statistics", "institution": "Example University", "graduation_year": "2021"}
        ],
        projects_analysis=[
            {
                "name": "Sales Analysis Dashboard",
                "technologies": ["Python", "SQL"],
                "description": "Dashboard for sales trends.",
                "achievements": ["Summarized sales performance by region."],
                "suggestions": ["Describe the audience and decisions supported."],
            }
        ],
        project_improvement_suggestions=[
            "Describe how verified project outcomes support the target role."
        ],
        ats_score=82,
        ats_score_explanation="Clear sections and relevant evidenced skills; quantify outcomes.",
        ats_matched_keywords=["SQL", "Python", "reporting"],
        ats_missing_keywords=["data visualization"],
        ats_formatting_issues=["Use consistent date formats."],
        ats_section_completeness={"skills": True, "education": True, "projects": True},
    )
    monkeypatch.setattr(
        resumes,
        "analyze_resume_ai",
        lambda _text, session_id, preferred_provider=None: (
            extracted_profile,
            "groq",
            "test-model",
        ),
    )
    demo = client.post("/api/v1/auth/demo").json()
    headers = {"Authorization": f"Bearer {demo['access_token']}"}
    resume_text = (
        "Resume Candidate - Data Analyst. SQL and Python reporting experience. "
        "Built data pipelines and sales analysis dashboards."
    )

    response = client.post(
        "/api/v1/resumes/analyze-text",
        json={"resume_text": resume_text, "preferred_provider": "groq", "replace_profile": True},
        headers=headers,
    )
    assert response.status_code == 200
    result_profile = response.json()["profile"]
    assert result_profile["ats_score"] == 82
    assert result_profile["ats_matched_keywords"] == ["SQL", "Python", "reporting"]
    assert result_profile["ats_missing_keywords"] == ["data visualization"]
    assert result_profile["ats_formatting_issues"] == ["Use consistent date formats."]
    assert result_profile["current_role"] == "Data Analyst"
    assert result_profile["total_experience"] == "3 years"
    assert result_profile["skills_by_category"] == {"Data": ["SQL", "Python"]}
    assert result_profile["experience_analysis"][0]["company"] == "Example Co"
    assert result_profile["education_analysis"][0]["graduation_year"] == "2021"
    assert result_profile["projects_analysis"][0]["technologies"] == ["Python", "SQL"]
    assert result_profile["ats_section_completeness"]["education"] is True
    assert set(result_profile["resume_analysis"]) == set(result_profile) & {
        "current_role",
        "total_experience",
        "summary_quality_analysis",
        "summary_improvement_suggestions",
        "skills_by_category",
        "target_role_skill_alignment",
        "experience_analysis",
        "education_analysis",
        "projects_analysis",
        "project_improvement_suggestions",
        "ats_score",
        "ats_score_explanation",
        "ats_matched_keywords",
        "ats_missing_keywords",
        "ats_formatting_issues",
        "ats_section_completeness",
    }

    saved_profile = client.get("/api/v1/profiles/me", headers=headers)
    assert saved_profile.status_code == 200
    saved_data = saved_profile.json()
    assert saved_data["target_role"] == "Data Analyst"
    assert saved_data["skills"] == ["SQL", "Python"]
    assert saved_data["experience"] == extracted_profile.experience
    assert saved_data["education"] == ["B.S. Statistics"]
    analysis = saved_data["resume_analysis"]
    assert analysis == result_profile["resume_analysis"]
    assert set(analysis) == {
        "current_role",
        "total_experience",
        "summary_quality_analysis",
        "summary_improvement_suggestions",
        "skills_by_category",
        "target_role_skill_alignment",
        "experience_analysis",
        "education_analysis",
        "projects_analysis",
        "project_improvement_suggestions",
        "ats_score",
        "ats_score_explanation",
        "ats_matched_keywords",
        "ats_missing_keywords",
        "ats_formatting_issues",
        "ats_section_completeness",
    }
    assert analysis["current_role"] == "Data Analyst"
    assert analysis["experience_analysis"][0]["company"] == "Example Co"
    assert analysis["education_analysis"][0]["graduation_year"] == "2021"
    assert analysis["projects_analysis"][0]["technologies"] == ["Python", "SQL"]
    assert analysis["ats_score"] == 82
    assert saved_data["ats_score"] == 82
    db = SessionLocal()
    persisted_profile = db.query(CandidateProfileModel).filter_by(
        user_id=demo["user"]["id"]
    ).one()
    persisted_analysis = persisted_profile.resume_analysis
    db.close()
    assert persisted_analysis == {
        "current_role": "Data Analyst",
        "total_experience": "3 years",
        "summary_quality_analysis": (
            "Relevant skills are visible, but the summary could be more concise."
        ),
        "summary_improvement_suggestions": [
            "Lead with the strongest evidenced analytics skill."
        ],
        "skills_by_category": {"Data": ["SQL", "Python"]},
        "target_role_skill_alignment": [
            "SQL is evidenced in project and work descriptions."
        ],
        "experience_analysis": [
            {
                "company": "Example Co",
                "job_title": "Data Analyst",
                "duration": "2022-2025",
                "responsibilities": ["Built sales reports."],
                "achievements": ["Automated recurring analysis."],
                "missing_measurable_results": [
                    "Add verified time savings if available."
                ],
                "suggestions": [
                    "Quantify the reporting improvement using a verified metric."
                ],
            }
        ],
        "education_analysis": [
            {
                "degree": "B.S. Statistics",
                "institution": "Example University",
                "graduation_year": "2021",
            }
        ],
        "projects_analysis": [
            {
                "name": "Sales Analysis Dashboard",
                "technologies": ["Python", "SQL"],
                "description": "Dashboard for sales trends.",
                "achievements": ["Summarized sales performance by region."],
                "suggestions": ["Describe the audience and decisions supported."],
            }
        ],
        "project_improvement_suggestions": [
            "Describe how verified project outcomes support the target role."
        ],
        "ats_score": 82,
        "ats_score_explanation": (
            "Clear sections and relevant evidenced skills; quantify outcomes."
        ),
        "ats_matched_keywords": ["SQL", "Python", "reporting"],
        "ats_missing_keywords": ["data visualization"],
        "ats_formatting_issues": ["Use consistent date formats."],
        "ats_section_completeness": {
            "skills": True,
            "education": True,
            "projects": True,
        },
    }

    upload_text = (
        "Uploaded resume for response-shape verification with distinct text and SQL experience."
    )
    uploaded = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("response-shape.txt", upload_text.encode(), "text/plain")},
        headers=headers,
    )
    assert uploaded.status_code == 200
    upload_profile = uploaded.json()["profile"]
    assert upload_profile["resume_analysis"] == analysis
    after_upload = client.get("/api/v1/profiles/me", headers=headers)
    assert after_upload.status_code == 200
    assert upload_profile["resume_analysis"] == after_upload.json()["resume_analysis"]


def test_resume_profile_sync_merges_by_default_and_replaces_only_with_consent(monkeypatch):
    import backend.routes.resumes as resumes

    token = client.post("/api/v1/auth/demo").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    user_id = client.get("/api/v1/auth/me", headers=headers).json()["id"]
    db = SessionLocal()
    existing = db.query(CandidateProfileModel).filter_by(user_id=user_id).one()
    existing.full_name = "User Edited Name"
    existing.email = "manual@example.com"
    existing.phone = "555-0101"
    existing.location = "New York"
    existing.target_role = "User Selected Role"
    existing.summary = "This is a user-edited professional summary that must be preserved."
    existing.skills = ["Existing Skill"]
    existing.experience = ["Manually edited experience entry."]
    existing.education = []
    existing.resume_analysis = {
        "ats_score": 91,
        "ats_matched_keywords": ["User-verified keyword"],
        "ats_missing_keywords": ["Existing missing keyword"],
    }
    db.commit()
    db.close()

    def mocked_analysis(text, session_id, preferred_provider=None):
        if "second resume" in text:
            profile = CandidateProfileData(
                full_name="Updated Resume Name",
                target_role="Updated Resume Role",
                summary="Updated summary from the second resume.",
                skills=["Updated Skill"],
                experience=["Updated experience entry."],
                ats_score=0,
                ats_score_explanation="",
                ats_matched_keywords=[],
            )
        else:
            profile = CandidateProfileData(
                full_name="Resume Name",
                phone="",
                location=None,
                target_role="Resume Target Role",
                summary="Summary extracted from the first resume.",
                skills=["Python"],
                experience=["New resume experience entry."],
                education=["B.S. Computer Science"],
                ats_score=None,
                ats_matched_keywords=[],
            )
        return profile, "groq", "test-model"

    monkeypatch.setattr(resumes, "analyze_resume_ai", mocked_analysis)
    first = client.post(
        "/api/v1/resumes/analyze-text",
        json={"resume_text": "The first resume has sufficient words for this profile merge test."},
        headers=headers,
    )
    assert first.status_code == 200

    db = SessionLocal()
    saved = db.query(CandidateProfileModel).filter_by(user_id=user_id).one()
    assert saved.full_name == "User Edited Name"
    assert saved.email == "manual@example.com"
    assert saved.phone == "555-0101"
    assert saved.location == "New York"
    assert saved.target_role == "User Selected Role"
    assert saved.summary.startswith("This is a user-edited")
    assert saved.skills == ["Existing Skill", "Python"]
    assert saved.experience == ["Manually edited experience entry.", "New resume experience entry."]
    assert saved.education == ["B.S. Computer Science"]
    assert saved.resume_analysis["ats_score"] == 91
    assert saved.resume_analysis["ats_matched_keywords"] == ["User-verified keyword"]
    db.close()

    second = client.post(
        "/api/v1/resumes/analyze-text",
        json={
            "resume_text": "The second resume has different sufficient words for replacement testing.",
            "replace_profile": True,
        },
        headers=headers,
    )
    assert second.status_code == 200

    db = SessionLocal()
    profiles = db.query(CandidateProfileModel).filter_by(user_id=user_id).all()
    assert len(profiles) == 1
    assert profiles[0].full_name == "Updated Resume Name"
    assert profiles[0].target_role == "Updated Resume Role"
    assert profiles[0].summary == "Updated summary from the second resume."
    assert profiles[0].skills == ["Updated Skill"]
    assert profiles[0].experience == ["Updated experience entry."]
    assert profiles[0].resume_analysis["ats_score"] == 0
    assert profiles[0].resume_analysis["ats_score_explanation"] == ""
    assert profiles[0].resume_analysis["ats_matched_keywords"] == []
    assert profiles[0].resume_analysis["ats_missing_keywords"] == ["Existing missing keyword"]
    db.close()


def test_resume_upload_rejects_empty_or_unreadable_text():
    token = client.post("/api/v1/auth/demo").json()["access_token"]
    response = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("empty.txt", b"Too short", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "Could not extract enough readable text" in response.json()["detail"]


def test_resume_text_endpoint_rejects_whitespace_only_input():
    token = client.post("/api/v1/auth/demo").json()["access_token"]
    response = client.post(
        "/api/v1/resumes/analyze-text",
        json={"resume_text": " " * 40},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
    assert "30 readable characters" in response.text


def test_resume_ai_provider_failure_returns_clear_error_without_saving_fake_results(monkeypatch):
    import backend.ai_engine as ai_engine
    import backend.routes.resumes as resumes

    def fail_analysis(*_args, **_kwargs):
        raise ai_engine.AIProviderUnavailable("All configured AI providers failed.")

    monkeypatch.setattr(resumes, "analyze_resume_ai", fail_analysis)
    token = client.post("/api/v1/auth/demo").json()["access_token"]
    user_id = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    ).json()["id"]
    db = SessionLocal()
    profiles_before = db.query(CandidateProfileModel).filter_by(user_id=user_id).count()
    db.close()
    response = client.post(
        "/api/v1/resumes/analyze-text",
        json={"resume_text": "Readable resume text with enough content for the AI provider failure test."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 503
    assert "providers failed" in response.json()["detail"]

    db = SessionLocal()
    assert db.query(ResumeRecordModel).filter_by(user_id=user_id).count() == 0
    assert db.query(CandidateProfileModel).filter_by(user_id=user_id).count() == profiles_before
    db.close()


@pytest.mark.parametrize(
    ("filename", "contents", "message"),
    [
        ("resume.doc", b"legacy word file", "Unsupported file format"),
        ("resume.pdf", b"not a valid PDF", "invalid or unreadable"),
        ("resume.docx", b"not a valid DOCX", "invalid or unreadable"),
    ],
)
def test_resume_upload_returns_actionable_error_for_unsupported_or_corrupt_files(
    filename, contents, message
):
    token = client.post("/api/v1/auth/demo").json()["access_token"]
    response = client.post(
        "/api/v1/resumes/upload",
        files={"file": (filename, contents, "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert message in response.json()["detail"]


def test_candidate_profile():
    token = client.post("/api/v1/auth/demo").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/profiles/me", headers=headers)
    assert res.status_code == 200
    profile = res.json()
    assert "skills" in profile
    assert profile["readiness_score"] >= 0
    assert profile["resume_analysis"]["experience_analysis"] == []
    assert profile["resume_analysis"]["ats_score"] is None

    # Update profile
    profile["summary"] = "Updated full stack developer summary testing persistence."
    put_res = client.put("/api/v1/profiles/me", json=profile, headers=headers)
    assert put_res.status_code == 200
    assert put_res.json()["summary"] == profile["summary"]


def test_profile_api_merges_and_explicitly_replaces_resume_analysis():
    token = client.post("/api/v1/auth/demo").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    updated = client.put(
        "/api/v1/profiles/me",
        json={
            "summary": "Manually edited profile summary to keep during analysis updates.",
            "resume_analysis": {
                "ats_score": 84,
                "ats_matched_keywords": ["Python", "SQL"],
                "ats_missing_keywords": ["data modeling"],
            }
        },
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["resume_analysis"]["ats_score"] == 84
    assert updated.json()["summary"] == (
        "Manually edited profile summary to keep during analysis updates."
    )

    ordinary_update = client.put(
        "/api/v1/profiles/me",
        json={
            "target_role": "Manually selected role",
            "summary": "A manually edited summary remains after an ordinary profile save.",
            "skills": ["User-verified Python"],
        },
        headers=headers,
    )
    assert ordinary_update.status_code == 200
    assert ordinary_update.json()["target_role"] == "Manually selected role"
    assert ordinary_update.json()["resume_analysis"]["ats_score"] == 84
    assert ordinary_update.json()["resume_analysis"]["ats_matched_keywords"] == [
        "Python",
        "SQL",
    ]

    empty_update = client.put(
        "/api/v1/profiles/me",
        json={
            "resume_analysis": {
                "ats_score": None,
                "ats_matched_keywords": [],
                "ats_missing_keywords": [],
            }
        },
        headers=headers,
    )
    assert empty_update.status_code == 200
    assert empty_update.json()["resume_analysis"]["ats_score"] == 84
    assert empty_update.json()["summary"] == (
        "A manually edited summary remains after an ordinary profile save."
    )
    assert empty_update.json()["target_role"] == "Manually selected role"
    assert empty_update.json()["resume_analysis"]["ats_matched_keywords"] == ["Python", "SQL"]
    assert empty_update.json()["resume_analysis"]["ats_missing_keywords"] == ["data modeling"]

    replacement = client.put(
        "/api/v1/profiles/me",
        json={
            "resume_analysis": {
                "ats_score": None,
                "ats_matched_keywords": [],
            },
            "replace_resume_analysis": True,
        },
        headers=headers,
    )
    assert replacement.status_code == 200
    assert replacement.json()["resume_analysis"]["ats_score"] is None
    assert replacement.json()["resume_analysis"]["ats_matched_keywords"] == []
    assert replacement.json()["resume_analysis"]["ats_missing_keywords"] == []


def test_candidate_context_includes_education_and_certifications_without_contact_details():
    from backend.profile_context import build_candidate_context

    profile = CandidateProfileModel(
        full_name="Context Test Candidate",
        email="private@example.com",
        phone="555-0199",
        education=["B.S. Computer Science"],
        certifications=["Cloud Practitioner"],
    )

    context = build_candidate_context(profile)

    assert "B.S. Computer Science" in context
    assert "Cloud Practitioner" in context
    assert "private@example.com" not in context
    assert "555-0199" not in context
    assert len(context) <= 5000


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


def test_ai_provider_preference_defaults_to_groq_and_falls_back(monkeypatch):
    from pydantic import BaseModel
    import backend.ai_engine as ai_engine

    class ExampleResponse(BaseModel):
        result: str

    monkeypatch.setattr(
        ai_engine,
        "get_configured_providers",
        lambda: ["gemini", "groq"],
    )
    monkeypatch.setattr(ai_engine, "check_rate_limits", lambda *args, **kwargs: None)
    calls = []

    def fail_groq(_prompt, _schema, model):
        calls.append(("groq", model))
        raise RuntimeError("provider details are not returned")

    def succeed_gemini(_prompt, _schema, model):
        calls.append(("gemini", model))
        return '{"result": "ok"}'

    monkeypatch.setattr(ai_engine, "_call_groq", fail_groq)
    monkeypatch.setattr(ai_engine, "_call_gemini", succeed_gemini)

    result, provider, model = ai_engine.execute_ai_json(
        "A unique test prompt",
        ExampleResponse,
        session_id=f"provider-fallback-{uuid4()}",
    )
    assert result.result == "ok"
    assert provider == "gemini"
    assert model == ai_engine.PROVIDER_MODELS["gemini"]
    assert [name for name, _ in calls] == ["groq", "gemini"]
    assert calls[0][1] == ai_engine.PROVIDER_MODELS["groq"]


def test_explicit_ai_provider_is_tried_before_other_configured_providers(monkeypatch):
    from pydantic import BaseModel
    import backend.ai_engine as ai_engine

    class ExampleResponse(BaseModel):
        result: str

    monkeypatch.setattr(
        ai_engine,
        "get_configured_providers",
        lambda: ["gemini", "groq"],
    )
    monkeypatch.setattr(ai_engine, "check_rate_limits", lambda *args, **kwargs: None)
    calls = []

    def succeed(provider):
        def call(_prompt, _schema, model):
            calls.append((provider, model))
            return '{"result": "ok"}'
        return call

    monkeypatch.setattr(ai_engine, "_call_groq", succeed("groq"))
    monkeypatch.setattr(ai_engine, "_call_gemini", succeed("gemini"))

    _, provider, _ = ai_engine.execute_ai_json(
        "Another unique test prompt",
        ExampleResponse,
        session_id=f"provider-selection-{uuid4()}",
        preferred_provider="gemini",
    )
    assert provider == "gemini"
    assert calls[0][0] == "gemini"


def test_ai_unavailable_error_identifies_providers_without_leaking_error_details(monkeypatch):
    from pydantic import BaseModel
    import backend.ai_engine as ai_engine

    class ExampleResponse(BaseModel):
        result: str

    class NotFoundError(Exception):
        pass

    class ServerError(Exception):
        pass

    def fail_with(error_type):
        def call(_prompt, _schema, _model):
            raise error_type("private provider response")
        return call

    monkeypatch.setattr(
        ai_engine,
        "get_configured_providers",
        lambda: ["groq", "gemini"],
    )
    monkeypatch.setattr(ai_engine, "check_rate_limits", lambda *args, **kwargs: None)
    monkeypatch.setattr(ai_engine, "_call_groq", fail_with(NotFoundError))
    monkeypatch.setattr(ai_engine, "_call_gemini", fail_with(ServerError))

    with pytest.raises(ai_engine.AIProviderUnavailable) as error:
        ai_engine.execute_ai_json(
            "A prompt for provider diagnostics",
            ExampleResponse,
            session_id=f"provider-diagnostics-{uuid4()}",
        )

    assert "groq: NotFoundError" in str(error.value)
    assert "gemini: ServerError" in str(error.value)
    assert "private provider response" not in str(error.value)


def test_invalid_structured_ai_output_falls_back_and_ats_scores_are_bounded(monkeypatch):
    from pydantic import BaseModel, ValidationError
    import backend.ai_engine as ai_engine

    class ExampleResponse(BaseModel):
        result: str

    calls = []

    monkeypatch.setattr(ai_engine, "get_configured_providers", lambda: ["groq", "gemini"])
    monkeypatch.setattr(ai_engine, "check_rate_limits", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        ai_engine,
        "_call_groq",
        lambda *_args: (calls.append("groq") or '{"unexpected": "field"}'),
    )
    monkeypatch.setattr(
        ai_engine,
        "_call_gemini",
        lambda *_args: (calls.append("gemini") or '{"result": "valid response"}'),
    )

    result, provider, _ = ai_engine.execute_ai_json(
        "A unique test prompt for invalid structured output.",
        ExampleResponse,
        session_id=f"invalid-json-{uuid4()}",
    )
    assert result.result == "valid response"
    assert provider == "gemini"
    assert calls == ["groq", "gemini"]
    with pytest.raises(ValidationError):
        CandidateProfileData(ats_score=101)


def test_resume_ai_falls_back_when_groq_omits_required_analysis_fields(monkeypatch, caplog):
    import json
    import backend.ai_engine as ai_engine

    complete_payload = _complete_resume_ai_payload()
    incomplete_payload = dict(complete_payload)
    for field in (
        "ats_score",
        "ats_score_explanation",
        "ats_matched_keywords",
        "ats_missing_keywords",
        "ats_formatting_issues",
        "ats_section_completeness",
        "projects_analysis",
    ):
        incomplete_payload.pop(field)

    calls = []
    monkeypatch.setattr(ai_engine, "get_configured_providers", lambda: ["groq", "gemini"])
    monkeypatch.setattr(ai_engine, "check_rate_limits", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        ai_engine,
        "_call_groq",
        lambda *_args: (calls.append("groq") or json.dumps(incomplete_payload)),
    )
    monkeypatch.setattr(
        ai_engine,
        "_call_gemini",
        lambda *_args: (calls.append("gemini") or json.dumps(complete_payload)),
    )
    resume_text = "Synthetic private resume marker used only to verify safe diagnostics."

    profile, provider, _ = ai_engine.analyze_resume_ai(
        resume_text,
        session_id=f"resume-complete-fallback-{uuid4()}",
    )

    assert calls == ["groq", "gemini"]
    assert provider == "gemini"
    assert profile.ats_score == 60
    assert profile.projects_analysis[0].name == "Sales dashboard"
    assert "omitted required fields" in caplog.text
    assert "ats_score" in caplog.text
    assert resume_text not in caplog.text


def test_resume_ai_falls_back_after_malformed_groq_json(monkeypatch, caplog):
    import json
    import backend.ai_engine as ai_engine

    complete_payload = _complete_resume_ai_payload()
    monkeypatch.setattr(ai_engine, "get_configured_providers", lambda: ["groq", "gemini"])
    monkeypatch.setattr(ai_engine, "check_rate_limits", lambda *args, **kwargs: None)
    monkeypatch.setattr(ai_engine, "_call_groq", lambda *_args: '{"ats_score":')
    monkeypatch.setattr(ai_engine, "_call_gemini", lambda *_args: json.dumps(complete_payload))
    resume_text = "Another synthetic private resume marker."

    profile, provider, _ = ai_engine.analyze_resume_ai(
        resume_text,
        session_id=f"resume-malformed-fallback-{uuid4()}",
    )

    assert provider == "gemini"
    assert profile.ats_score == 60
    assert "not valid JSON" in caplog.text
    assert resume_text not in caplog.text


def test_resume_ai_accepts_complete_structured_groq_response(monkeypatch):
    import json
    import backend.ai_engine as ai_engine

    payload = _complete_resume_ai_payload()
    monkeypatch.setattr(ai_engine, "get_configured_providers", lambda: ["groq"])
    monkeypatch.setattr(ai_engine, "check_rate_limits", lambda *args, **kwargs: None)
    monkeypatch.setattr(ai_engine, "_call_groq", lambda *_args: json.dumps(payload))

    profile, provider, model = ai_engine.analyze_resume_ai(
        "A synthetic resume with stated education, work, skills, and projects.",
        session_id=f"resume-complete-groq-{uuid4()}",
    )

    assert provider == "groq"
    assert model == ai_engine.PROVIDER_MODELS["groq"]
    assert profile.ats_score == 60
    assert profile.ats_score_explanation
    assert profile.education_analysis[0].degree == "B.S. Statistics"
    assert profile.projects_analysis[0].name == "Sales dashboard"


def test_resume_upload_returns_clear_error_without_saving_incomplete_ats_output(monkeypatch, caplog):
    import json
    import backend.ai_engine as ai_engine

    incomplete_payload = _complete_resume_ai_payload()
    incomplete_payload["ats_score"] = None
    incomplete_payload["ats_score_explanation"] = ""
    incomplete_payload["ats_section_completeness"] = {}

    monkeypatch.setattr(ai_engine, "get_configured_providers", lambda: ["groq"])
    monkeypatch.setattr(ai_engine, "check_rate_limits", lambda *args, **kwargs: None)
    monkeypatch.setattr(ai_engine, "_call_groq", lambda *_args: json.dumps(incomplete_payload))
    resume_text = "Unique synthetic resume marker; no real candidate details are used here."
    token = client.post("/api/v1/auth/demo").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    user_id = client.get("/api/v1/auth/me", headers=headers).json()["id"]

    response = client.post(
        "/api/v1/resumes/analyze-text",
        json={"resume_text": resume_text, "preferred_provider": "groq"},
        headers=headers,
    )

    assert response.status_code == 503
    assert "incomplete structured response" in response.json()["detail"]
    assert resume_text not in caplog.text
    db = SessionLocal()
    try:
        assert db.query(ResumeRecordModel).filter_by(user_id=user_id).count() == 0
        assert db.query(SavedReportModel).filter_by(user_id=user_id).count() == 0
    finally:
        db.close()


def test_groq_gpt_oss_uses_json_schema_mode_without_live_provider_call(monkeypatch):
    import json
    import sys
    from types import SimpleNamespace
    import backend.ai_engine as ai_engine

    captured_requests = []

    class FakeGroq:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=self._create_completion)
            )

        def _create_completion(self, **kwargs):
            captured_requests.append(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="{}"))]
            )

    monkeypatch.setenv("GROQ_API_KEY", "unit-test-key-not-a-real-credential")
    monkeypatch.setitem(sys.modules, "groq", SimpleNamespace(Groq=FakeGroq))
    schema = json.dumps(CandidateProfileData.model_json_schema())

    ai_engine._call_groq("synthetic prompt", schema, "openai/gpt-oss-20b")
    ai_engine._call_groq("synthetic prompt", schema, "llama-3.3-70b-versatile")

    assert captured_requests[0]["response_format"]["type"] == "json_schema"
    assert captured_requests[0]["response_format"]["json_schema"]["strict"] is False
    assert "ats_score" in captured_requests[0]["response_format"]["json_schema"]["schema"]["properties"]
    assert captured_requests[1]["response_format"] == {"type": "json_object"}


def test_incomplete_latest_resume_is_not_returned_or_reused(monkeypatch):
    import backend.routes.resumes as resumes

    demo = client.post("/api/v1/auth/demo").json()
    headers = {"Authorization": f"Bearer {demo['access_token']}"}
    raw_text = "A sufficiently long synthetic resume used to test stale cached analyses."
    profile_payload = _complete_resume_ai_payload()
    profile_payload["_provided_fields"] = sorted(
        set(CandidateProfileData.model_fields) - {"ats_score", "ats_score_explanation"}
    )
    profile_payload["_provider_used"] = "groq"
    profile_payload["_model_used"] = "openai/gpt-oss-20b"
    db = SessionLocal()
    try:
        db.add(
            ResumeRecordModel(
                user_id=demo["user"]["id"],
                filename="old-analysis.txt",
                file_type="text",
                raw_text=raw_text,
                parsed_profile=profile_payload,
            )
        )
        db.commit()
    finally:
        db.close()

    old_latest = client.get("/api/v1/resumes/latest", headers=headers)
    assert old_latest.status_code == 503
    assert raw_text not in old_latest.text

    monkeypatch.setattr(
        resumes,
        "analyze_resume_ai",
        lambda *_args, **_kwargs: (
            CandidateProfileData.model_validate(_complete_resume_ai_payload()),
            "groq",
            "fresh-test-model",
        ),
    )
    refreshed = client.post(
        "/api/v1/resumes/analyze-text",
        json={"resume_text": raw_text, "preferred_provider": "groq"},
        headers=headers,
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["model_used"] == "fresh-test-model"
    assert refreshed.json()["profile"]["ats_score"] == 60
    latest = client.get("/api/v1/resumes/latest", headers=headers)
    assert latest.status_code == 200
    assert latest.json()["model_used"] == "fresh-test-model"


def test_switching_ai_provider_allows_same_prompt_during_duplicate_cooldown(monkeypatch):
    from datetime import date
    import backend.ai_engine as ai_engine

    monkeypatch.setattr(ai_engine, "_recent_requests", {})
    monkeypatch.setattr(ai_engine, "_session_usage", {})
    monkeypatch.setattr(ai_engine, "_global_usage", 0)
    monkeypatch.setattr(ai_engine, "_usage_day", date.today())
    session_id = f"provider-cooldown-{uuid4()}"
    prompt = "Same prompt, intentionally selecting another model."

    ai_engine.check_rate_limits(session_id, prompt, preferred_provider="groq")
    ai_engine.check_rate_limits(session_id, prompt, preferred_provider="gemini")
    with pytest.raises(ai_engine.RateLimitError):
        ai_engine.check_rate_limits(session_id, prompt, preferred_provider="gemini")


def test_resume_retry_reuses_recent_analysis(monkeypatch):
    import backend.routes.resumes as resumes

    token = client.post("/api/v1/auth/demo").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    user_id = client.get("/api/v1/auth/me", headers=headers).json()["id"]
    raw_text = "A sufficiently detailed candidate resume with Python, React, and API development experience."
    monkeypatch.setattr(
        resumes,
        "analyze_resume_ai",
        lambda text, session_id, preferred_provider=None: (
            CandidateProfileData.model_validate(_complete_resume_ai_payload()),
            "Test provider",
            "test-model",
        ),
    )

    db = SessionLocal()
    resumes_before = db.query(ResumeRecordModel).filter_by(user_id=user_id).count()
    reports_before = db.query(SavedReportModel).filter_by(user_id=user_id, report_type="resume").count()
    db.close()

    first = client.post("/api/v1/resumes/analyze-text", json={"resume_text": raw_text}, headers=headers)
    second = client.post("/api/v1/resumes/analyze-text", json={"resume_text": raw_text}, headers=headers)
    assert first.status_code == second.status_code == 200
    assert second.json()["provider_used"] == "Test provider"
    assert second.json()["model_used"] == "test-model"

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


def test_interview_questions_route_works_with_mocked_ai(monkeypatch):
    from backend.schemas import InterviewQuestionItem
    import backend.routes.interviews as interviews

    received = {}

    def generate_questions(**kwargs):
        received.update(kwargs)
        return (
            [
                InterviewQuestionItem(
                    id="question-1",
                    question="How would you design a reliable API?",
                    type="technical",
                    difficulty="Medium",
                )
            ],
            "groq",
            "test-model",
        )

    monkeypatch.setattr(
        interviews,
        "generate_interview_questions_ai",
        generate_questions,
    )
    token = client.post("/api/v1/auth/demo").json()["access_token"]
    user_id = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    ).json()["id"]
    db = SessionLocal()
    profile = db.query(CandidateProfileModel).filter_by(user_id=user_id).one()
    profile.email = "private@example.com"
    profile.target_role = "Backend Engineer"
    profile.skills = ["Python", "FastAPI"]
    profile.experience = ["Built authenticated REST APIs."]
    profile.projects = ["Created a task management service."]
    db.commit()
    db.close()
    response = client.post(
        "/api/v1/interviews/questions",
        json={
            "target_role": "Backend Engineer",
            "interview_type": "technical",
            "level": "Entry-level",
            "preferred_provider": "groq",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["questions"][0]["id"] == "question-1"
    assert received["preferred_provider"] == "groq"
    assert "Python" in received["candidate_context"]
    assert "authenticated REST APIs" in received["candidate_context"]
    assert "private@example.com" not in received["candidate_context"]


def test_project_generation_accepts_frontend_interest_text(monkeypatch):
    from backend.schemas import ProjectBriefData
    import backend.routes.projects as projects

    received = {}
    def generate_projects(**kwargs):
        received.update(kwargs)
        return (
            [
                ProjectBriefData(
                    title="Skills Portfolio",
                    problem_statement="Build a portfolio that demonstrates practical skills.",
                )
            ],
            "groq",
            "test-model",
        )

    monkeypatch.setattr(
        projects,
        "generate_project_recommendations_ai",
        generate_projects,
    )
    token = client.post("/api/v1/auth/demo").json()["access_token"]
    user_id = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    ).json()["id"]
    db = SessionLocal()
    profile = db.query(CandidateProfileModel).filter_by(user_id=user_id).one()
    profile.target_role = "Data Engineer"
    profile.skills = ["Python", "SQL"]
    profile.experience = ["Maintained data pipelines."]
    db.commit()
    db.close()
    response = client.post(
        "/api/v1/projects/generate",
        json={
            "interests": "AI career tools, distributed systems",
            "skills": ["Python"],
            "domain": "Full Stack & Applied AI",
            "difficulty": "Intermediate",
            "preferred_provider": "groq",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()[0]["title"] == "Skills Portfolio"
    assert received["candidate_context"]


def test_roadmap_milestone_toggle_is_persisted(monkeypatch):
    from backend.schemas import CareerRoadmapData, MilestoneItem
    import backend.routes.roadmaps as roadmaps

    roadmap_data = CareerRoadmapData(
        career_goal="Backend Engineer",
        milestones=[
            MilestoneItem(
                week=1,
                title="Build an API",
                learning_tasks=["Implement one endpoint"],
                deliverable="A working API",
                completed=False,
            )
        ],
    )
    received = {}
    def generate_roadmap(**kwargs):
        received.update(kwargs)
        return roadmap_data, "groq", "test-model"

    monkeypatch.setattr(roadmaps, "generate_roadmap_ai", generate_roadmap)
    token = client.post("/api/v1/auth/demo").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    user_id = client.get("/api/v1/auth/me", headers=headers).json()["id"]
    db = SessionLocal()
    profile = db.query(CandidateProfileModel).filter_by(user_id=user_id).one()
    profile.target_role = "Backend Engineer"
    profile.skills = ["Python"]
    profile.experience = ["Built production APIs."]
    db.commit()
    db.close()
    generated = client.post(
        "/api/v1/roadmaps/generate",
        json={
            "skills": ["Python"],
            "career_goal": "Backend Engineer",
            "experience_level": "Entry-level",
            "duration_weeks": 8,
            "preferred_provider": "groq",
        },
        headers=headers,
    )
    assert generated.status_code == 200
    assert "Built production APIs." in received["candidate_context"]
    roadmap_id = generated.json()["id"]

    updated = client.put(
        f"/api/v1/roadmaps/{roadmap_id}/milestone",
        json={"week": 1, "completed": True},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["milestones"][0]["completed"] is True

    persisted = client.get("/api/v1/roadmaps/latest", headers=headers)
    assert persisted.status_code == 200
    assert persisted.json()["milestones"][0]["completed"] is True
    assert persisted.json()["progress_percent"] == 100


def test_reports_lifecycle():
    token = client.post("/api/v1/auth/demo").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # List reports
    res = client.get("/api/v1/reports", headers=headers)
    assert res.status_code == 200
    reports = res.json()
    assert isinstance(reports, list)
