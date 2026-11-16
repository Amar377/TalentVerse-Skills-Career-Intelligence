"""Project Recommendations routes — with deduplication guards."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from backend.database import get_db, User, ProjectBriefModel, SavedReportModel, CandidateProfileModel
from backend.schemas import (
    ProjectGenerateRequest,
    ProjectBriefOut,
    ProjectBriefData,
)
from backend.auth_utils import get_current_user
from backend.ai_engine import generate_project_recommendations_ai
from backend.profile_context import build_candidate_context

router = APIRouter(prefix="/projects", tags=["Project Recommendations"])


@router.post("/generate", response_model=List[ProjectBriefOut])
def generate_projects_endpoint(
    payload: ProjectGenerateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    skills = payload.skills
    profile = (
        db.query(CandidateProfileModel)
        .filter(CandidateProfileModel.user_id == user.id)
        .order_by(CandidateProfileModel.updated_at.desc(), CandidateProfileModel.created_at.desc())
        .first()
    )
    if not skills:
        skills = profile.skills if profile and profile.skills else []

    # Deduplication: if the user already has project briefs for this exact domain+difficulty
    # generated within the last 60 seconds, return the existing ones instead of regenerating.
    # This prevents accidental double-clicks and rapid re-submissions from creating duplicate records.
    domain = payload.domain or "General"
    difficulty = payload.difficulty or "Intermediate"
    dedup_window = datetime.utcnow() - timedelta(seconds=60)

    recent_duplicates = (
        db.query(ProjectBriefModel)
        .filter(
            ProjectBriefModel.user_id == user.id,
            ProjectBriefModel.domain == domain,
            ProjectBriefModel.difficulty == difficulty,
            ProjectBriefModel.created_at >= dedup_window,
        )
        .order_by(ProjectBriefModel.created_at.desc())
        .all()
    )
    if recent_duplicates:
        # Return the most recent batch (up to 3) instead of re-generating
        return [ProjectBriefOut.model_validate(r) for r in recent_duplicates[:3]]

    projects, provider, model = generate_project_recommendations_ai(
        interests=payload.interests,
        skills=skills,
        domain=domain,
        difficulty=difficulty,
        session_id=user.id,
        preferred_provider=payload.preferred_provider,
        candidate_context=build_candidate_context(profile),
    )

    saved_briefs = []
    for p in projects:
        record = ProjectBriefModel(
            user_id=user.id,
            title=p.title,
            problem_statement=p.problem_statement,
            domain=p.domain,
            difficulty=p.difficulty,
            target_users=p.target_users,
            core_features=p.core_features,
            suggested_tech_stack=p.suggested_tech_stack,
            implementation_milestones=p.implementation_milestones,
            evaluation_metrics=p.evaluation_metrics,
            portfolio_description=p.portfolio_description,
        )
        db.add(record)
        saved_briefs.append(record)

    # Save to Saved Reports — deduplicate by checking for identical title in last 60 seconds
    report_title = f"Project Recommendations \u2014 {domain}"
    existing_report = (
        db.query(SavedReportModel)
        .filter(
            SavedReportModel.user_id == user.id,
            SavedReportModel.report_type == "project",
            SavedReportModel.title == report_title,
            SavedReportModel.created_at >= dedup_window,
        )
        .first()
    )
    if not existing_report:
        report = SavedReportModel(
            user_id=user.id,
            report_type="project",
            title=report_title,
            summary=f"Generated {len(projects)} tailored portfolio project architecture briefs for {difficulty} level.",
            score=len(projects) * 30,
            tags=["Project Brief", difficulty, domain],
            data={
                "projects": [p.model_dump() for p in projects],
                "interests": payload.interests,
                "provider": provider,
                "model": model,
            },
        )
        db.add(report)

    db.commit()

    for r in saved_briefs:
        db.refresh(r)

    return [ProjectBriefOut.model_validate(r) for r in saved_briefs]


@router.get("", response_model=List[ProjectBriefOut])
def list_projects(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Return the most recent 9 project briefs (3 batches maximum) to prevent unbounded list growth
    records = (
        db.query(ProjectBriefModel)
        .filter(ProjectBriefModel.user_id == user.id)
        .order_by(ProjectBriefModel.created_at.desc())
        .limit(9)
        .all()
    )
    return [ProjectBriefOut.model_validate(r) for r in records]
