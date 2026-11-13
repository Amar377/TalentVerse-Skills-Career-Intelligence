"""Dashboard analytics and career intelligence metrics."""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import (
    get_db,
    User,
    CandidateProfileModel,
    RoadmapModel,
    JobMatchModel,
    InterviewModel,
    SavedReportModel,
)
from backend.schemas import (
    DashboardStatsOut,
    SkillDistributionItem,
    RecentActivityItem,
)
from backend.auth_utils import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardStatsOut)
def get_dashboard_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(CandidateProfileModel)
        .filter(CandidateProfileModel.user_id == user.id)
        .order_by(CandidateProfileModel.updated_at.desc(), CandidateProfileModel.created_at.desc())
        .first()
    )
    candidate_name = (profile.full_name if profile and profile.full_name else user.full_name) or "Candidate"
    target_role = (profile.target_role if profile and profile.target_role else "Not set")
    readiness_score = profile.readiness_score if profile and profile.readiness_score is not None else 0

    # Roadmap progress
    roadmap = (
        db.query(RoadmapModel)
        .filter(RoadmapModel.user_id == user.id)
        .order_by(RoadmapModel.created_at.desc())
        .first()
    )
    completed_milestones = 0
    total_milestones = 0
    if roadmap and roadmap.milestones:
        total_milestones = len(roadmap.milestones)
        completed_milestones = sum(1 for m in roadmap.milestones if m.get("completed"))

    # Recent job match score
    latest_job = (
        db.query(JobMatchModel)
        .filter(JobMatchModel.user_id == user.id)
        .order_by(JobMatchModel.created_at.desc())
        .first()
    )
    job_fit_score = latest_job.match_score_percent if latest_job else None

    # Skills distribution
    raw_skills = profile.skills if profile and profile.skills else []
    raw_soft_skills = profile.soft_skills if profile and profile.soft_skills else []
    skills_list = list({skill.strip().casefold(): skill.strip() for skill in raw_skills if isinstance(skill, str) and skill.strip()}.values())
    soft_skills_list = list({skill.strip().casefold(): skill.strip() for skill in raw_soft_skills if isinstance(skill, str) and skill.strip()}.values())

    skills_distribution: List[SkillDistributionItem] = []
    for skill in skills_list:
        skills_distribution.append(
            SkillDistributionItem(
                category="Technical",
                name=skill,
                type="technical",
            )
        )

    for s_skill in soft_skills_list:
        skills_distribution.append(
            SkillDistributionItem(
                category="Professional",
                name=s_skill,
                type="soft",
            )
        )

    # Recent activities
    recent_activities: List[RecentActivityItem] = []
    reports = (
        db.query(SavedReportModel)
        .filter(SavedReportModel.user_id == user.id)
        .order_by(SavedReportModel.created_at.desc())
        .limit(6)
        .all()
    )
    for r in reports:
        recent_activities.append(
            RecentActivityItem(
                id=r.id,
                type=r.report_type,
                title=r.title,
                description=r.summary or "Generated career intelligence report.",
                timestamp=r.created_at or datetime.utcnow(),
                score=r.score,
            )
        )

    # Dynamic recommended actions
    recommended_actions = []
    if not roadmap:
        recommended_actions.append({
            "title": "Generate Career Roadmap",
            "action": "/app/roadmap",
            "reason": f"Map your skill gaps to target the '{target_role}' role.",
            "urgency": "High",
        })
    elif completed_milestones < total_milestones:
        next_week = completed_milestones + 1
        recommended_actions.append({
            "title": f"Complete Milestone Week {next_week}",
            "action": "/app/roadmap",
            "reason": "Stay on track to reach job-readiness targets.",
            "urgency": "Medium",
        })

    if not latest_job:
        recommended_actions.append({
            "title": "Run Job Match Analysis",
            "action": "/app/job-matcher",
            "reason": "Test your current profile against a live job description.",
            "urgency": "High",
        })
    else:
        recommended_actions.append({
            "title": "Practice Interview Questions",
            "action": "/app/interview-coach",
            "reason": f"Prepare for technical screening for {target_role}.",
            "urgency": "Medium",
        })

    recommended_actions.append({
        "title": "Explore Portfolio Projects",
        "action": "/app/projects",
        "reason": "Build production-grade projects that prove unverified skills.",
        "urgency": "Low",
    })

    return DashboardStatsOut(
        candidate_name=candidate_name,
        target_role=target_role,
        career_readiness_score=readiness_score,
        skills_count=len(skills_list) + len(soft_skills_list),
        completed_milestones=completed_milestones,
        total_milestones=total_milestones,
        recent_job_fit_score=job_fit_score,
        skills_distribution=skills_distribution,
        recent_activities=recent_activities,
        recommended_actions=recommended_actions,
    )
