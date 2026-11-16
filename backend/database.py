"""Database models and session management."""
import datetime
import uuid
from typing import Generator
from sqlalchemy import (
    create_engine, Column, String, Integer, Text, Boolean, DateTime, ForeignKey, JSON, inspect, text
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from backend.config import DB_URL

# SQLite connect args
connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}

engine = create_engine(DB_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="candidate")
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    profiles = relationship("CandidateProfileModel", back_populates="user", cascade="all, delete-orphan")
    resume_records = relationship("ResumeRecordModel", back_populates="user", cascade="all, delete-orphan")
    roadmaps = relationship("RoadmapModel", back_populates="user", cascade="all, delete-orphan")
    job_matches = relationship("JobMatchModel", back_populates="user", cascade="all, delete-orphan")
    project_briefs = relationship("ProjectBriefModel", back_populates="user", cascade="all, delete-orphan")
    interview_sessions = relationship("InterviewModel", back_populates="user", cascade="all, delete-orphan")
    saved_reports = relationship("SavedReportModel", back_populates="user", cascade="all, delete-orphan")


class CandidateProfileModel(Base):
    __tablename__ = "candidate_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    target_role = Column(String(255), nullable=True)
    experience_level = Column(String(100), default="Entry-level")
    summary = Column(Text, nullable=True)

    skills = Column(JSON, default=list)
    soft_skills = Column(JSON, default=list)
    experience = Column(JSON, default=list)
    education = Column(JSON, default=list)
    certifications = Column(JSON, default=list)
    projects = Column(JSON, default=list)
    missing_information = Column(JSON, default=list)
    strengths = Column(JSON, default=list)
    improvement_recommendations = Column(JSON, default=list)
    readiness_score = Column(Integer, default=0)
    resume_analysis = Column(JSON, default=dict, server_default=text("'{}'"), nullable=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="profiles")


class ResumeRecordModel(Base):
    __tablename__ = "resume_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    filename = Column(String(255), nullable=True)
    file_type = Column(String(50), default="text")
    raw_text = Column(Text, nullable=False)
    parsed_profile = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="resume_records")


class RoadmapModel(Base):
    __tablename__ = "roadmaps"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    career_goal = Column(String(255), nullable=False)
    experience_level = Column(String(100), default="Student")
    duration_weeks = Column(Integer, default=8)
    skill_gaps = Column(JSON, default=list)
    milestones = Column(JSON, default=list)
    assumptions_or_missing_information = Column(JSON, default=list)
    recommended_resources = Column(JSON, default=list)
    progress_percent = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="roadmaps")


class JobMatchModel(Base):
    __tablename__ = "job_matches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    target_role = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    job_description = Column(Text, nullable=False)
    match_score_percent = Column(Integer, default=0)
    matching_skills = Column(JSON, default=list)
    missing_or_unverified_skills = Column(JSON, default=list)
    experience_relevance = Column(JSON, default=list)
    education_relevance = Column(JSON, default=list)
    strengths = Column(JSON, default=list)
    evidence = Column(JSON, default=list)
    improvement_actions = Column(JSON, default=list)
    caveat = Column(String(255), default="AI-generated estimate, not a hiring decision.")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="job_matches")


class ProjectBriefModel(Base):
    __tablename__ = "project_briefs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    problem_statement = Column(Text, nullable=False)
    domain = Column(String(100), default="General")
    difficulty = Column(String(50), default="Intermediate")
    target_users = Column(JSON, default=list)
    core_features = Column(JSON, default=list)
    suggested_tech_stack = Column(JSON, default=list)
    implementation_milestones = Column(JSON, default=list)
    evaluation_metrics = Column(JSON, default=list)
    portfolio_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="project_briefs")


class InterviewModel(Base):
    __tablename__ = "interviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    target_role = Column(String(255), nullable=False)
    interview_type = Column(String(50), default="technical")  # technical or behavioral
    question = Column(Text, nullable=False)
    user_answer = Column(Text, nullable=True)
    answer_score = Column(Integer, default=0)
    feedback = Column(Text, nullable=True)
    strengths = Column(JSON, default=list)
    improvement_areas = Column(JSON, default=list)
    missing_concepts = Column(JSON, default=list)
    suggested_answer = Column(Text, nullable=True)
    practice_tasks = Column(JSON, default=list)
    next_session_focus = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="interview_sessions")


class SavedReportModel(Base):
    __tablename__ = "saved_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    report_type = Column(String(50), nullable=False)  # resume, roadmap, job_match, project, interview
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
    tags = Column(JSON, default=list)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="saved_reports")


def migrate_candidate_profile_resume_analysis(bind: Engine = engine) -> None:
    """Add the resume-analysis column to databases created before it was introduced."""
    if "candidate_profiles" not in inspect(bind).get_table_names():
        return

    try:
        with bind.begin() as connection:
            columns = {
                column["name"]
                for column in inspect(connection).get_columns("candidate_profiles")
            }
            if "resume_analysis" not in columns:
                column_type = CandidateProfileModel.__table__.c.resume_analysis.type.compile(
                    dialect=connection.dialect
                )
                connection.execute(
                    text(
                        "ALTER TABLE candidate_profiles "
                        f"ADD COLUMN resume_analysis {column_type} NOT NULL DEFAULT '{{}}'"
                    )
                )
    except OperationalError:
        # Another process may have added the same column after our initial inspection.
        columns = {
            column["name"]
            for column in inspect(bind).get_columns("candidate_profiles")
        }
        if "resume_analysis" not in columns:
            raise


def init_db(bind: Engine = engine):
    Base.metadata.create_all(bind=bind)
    migrate_candidate_profile_resume_analysis(bind)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
