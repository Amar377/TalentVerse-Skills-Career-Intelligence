"""Authentication and session routes."""
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.config import ACCESS_TOKEN_EXPIRE_MINUTES
from backend.database import (
    get_db,
    User,
    CandidateProfileModel,
    ResumeRecordModel,
    RoadmapModel,
    JobMatchModel,
    ProjectBriefModel,
    InterviewModel,
    SavedReportModel,
)
from backend.schemas import UserCreate, UserLogin, UserOut, Token
from backend.auth_utils import (
    DEMO_EMAIL_DOMAIN,
    DEMO_EMAIL_PREFIX,
    create_access_token,
    get_current_user,
    hash_password,
    is_temporary_demo_user,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
DEMO_SESSION_RETENTION = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES, hours=1)


def cleanup_expired_demo_sessions(db: Session) -> int:
    cutoff = datetime.utcnow() - DEMO_SESSION_RETENTION
    expired_users = (
        db.query(User)
        .filter(
            User.is_demo.is_(True),
            User.email.like(f"{DEMO_EMAIL_PREFIX}%{DEMO_EMAIL_DOMAIN}"),
            User.created_at < cutoff,
        )
        .all()
    )
    expired_user_ids = [
        user.id for user in expired_users if is_temporary_demo_user(user)
    ]
    if not expired_user_ids:
        return 0

    for model in (
        CandidateProfileModel,
        ResumeRecordModel,
        RoadmapModel,
        JobMatchModel,
        ProjectBriefModel,
        InterviewModel,
        SavedReportModel,
    ):
        (
            db.query(model)
            .filter(model.user_id.in_(expired_user_ids))
            .delete(synchronize_session=False)
        )
    return (
        db.query(User)
        .filter(User.id.in_(expired_user_ids))
        .delete(synchronize_session=False)
    )


@router.post("/register", response_model=Token)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    user = User(
        email=user_data.email.lower(),
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        role="candidate",
        is_demo=False,
    )
    try:
        db.add(user)
        db.flush()

        # Create the account and its initial profile in one transaction.
        profile = CandidateProfileModel(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            summary="",
            skills=[],
        )
        db.add(profile)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    token = create_access_token({"sub": user.id, "email": user.email})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email.lower()).first()
    if not user or user.is_demo or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # Upgrade legacy deterministic-salt hashes after a successful login.
    if "$" not in user.hashed_password:
        user.hashed_password = hash_password(login_data.password)
        db.commit()

    token = create_access_token({"sub": user.id, "email": user.email})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/demo", response_model=Token)
def demo_login(db: Session = Depends(get_db)):
    """One-click guest/demo login with full access to sandbox features."""
    demo_email = f"{DEMO_EMAIL_PREFIX}{uuid4().hex}{DEMO_EMAIL_DOMAIN}"
    demo_user = User(
        email=demo_email,
        hashed_password=hash_password(uuid4().hex),
        full_name="Alex Morgan",
        role="candidate",
        is_demo=True,
    )
    db.add(demo_user)
    db.flush()

    profile = CandidateProfileModel(
        user_id=demo_user.id,
        full_name="Alex Morgan",
        email=demo_email,
        phone="+1 (555) 019-2834",
        location="San Francisco, CA",
        target_role="Full Stack Engineer",
        experience_level="Entry-level",
        summary="Passionate software engineer skilled in React, TypeScript, Python, and cloud infrastructure. Builder of AI-augmented SaaS applications and scalable web systems.",
        skills=["Python", "FastAPI", "React", "TypeScript", "SQL", "Git", "Docker", "Tailwind CSS", "REST APIs"],
        soft_skills=["Problem Solving", "Team Collaboration", "Agile Development", "System Design"],
        experience=[
            "Software Engineering Fellow — TechLabs (2024): Developed modular full-stack web applications and automated data pipelines.",
            "Undergraduate Teaching Assistant — Computer Science Dept (2023): Mentored 40+ students in data structures and Python programming."
        ],
        education=[
            "B.S. in Computer Science — California Institute of Technology (2024)"
        ],
        certifications=[
            "AWS Certified Cloud Practitioner",
            "Meta Front-End Developer Professional Certificate"
        ],
        projects=[
            "TalentVerse: AI-powered career intelligence SaaS platform with multi-provider fallbacks and dynamic skill roadmapping.",
            "CloudPulse: Real-time telemetry dashboard monitoring service health and p99 latency metrics."
        ],
        missing_information=[
            "Quantified production metrics on recent fellowship work",
            "Verified portfolio links on profile"
        ],
        strengths=[
            "Strong modern full-stack developer skill set across Python and TypeScript",
            "Proven aptitude for AI workflow integration and responsive UI design",
            "Solid computer science fundamentals and structured approach to problem solving"
        ],
        improvement_recommendations=[
            "Add metrics indicating system scale or performance gains in project descriptions",
            "Complete advanced distributed systems and database indexing milestones",
            "Practice high-level system architecture interview questions"
        ],
        readiness_score=85,
    )
    db.add(profile)
    db.commit()
    db.refresh(demo_user)

    token = create_access_token({"sub": demo_user.id, "email": demo_user.email})
    return Token(access_token=token, user=UserOut.model_validate(demo_user))


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)
