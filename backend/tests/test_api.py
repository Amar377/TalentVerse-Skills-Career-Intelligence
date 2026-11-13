"""Comprehensive automated test suite for TalentVerse 2.0 API."""
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal, User, CandidateProfileModel, ResumeRecordModel, SavedReportModel
from backend.schemas import CandidateProfileData
from backend.auth_utils import hash_password, verify_password
import os
import pytest

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
    assert data["user"]["email"] == "demo@talentverse.ai"

    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "demo@talentverse.ai"


def test_protected_routes_reject_missing_and_invalid_tokens():
    assert client.get("/api/v1/profiles/me").status_code == 401
    assert client.get(
        "/api/v1/profiles/me",
        headers={"Authorization": "Bearer invalid-token"},
    ).status_code == 401


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
