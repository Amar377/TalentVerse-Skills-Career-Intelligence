"""Career Roadmap routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db, User, RoadmapModel, SavedReportModel, CandidateProfileModel
from backend.schemas import (
    RoadmapGenerateRequest,
    RoadmapOut,
    MilestoneToggleRequest,
)
from backend.auth_utils import get_current_user
from backend.ai_engine import generate_roadmap_ai
from backend.profile_context import build_candidate_context

router = APIRouter(prefix="/roadmaps", tags=["Career Roadmaps"])


@router.post("/generate", response_model=RoadmapOut)
def generate_roadmap(
    payload: RoadmapGenerateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(CandidateProfileModel)
        .filter(CandidateProfileModel.user_id == user.id)
        .order_by(CandidateProfileModel.updated_at.desc(), CandidateProfileModel.created_at.desc())
        .first()
    )
    roadmap_data, provider, model = generate_roadmap_ai(
        skills=payload.skills,
        goal=payload.career_goal,
        level=payload.experience_level,
        weeks=payload.duration_weeks,
        session_id=user.id,
        preferred_provider=payload.preferred_provider,
        candidate_context=build_candidate_context(profile),
    )

    roadmap_record = RoadmapModel(
        user_id=user.id,
        career_goal=payload.career_goal,
        experience_level=payload.experience_level,
        duration_weeks=payload.duration_weeks,
        skill_gaps=roadmap_data.skill_gaps,
        milestones=[m.model_dump() for m in roadmap_data.milestones],
        assumptions_or_missing_information=roadmap_data.assumptions_or_missing_information,
        recommended_resources=roadmap_data.recommended_resources,
        progress_percent=roadmap_data.progress_percent,
    )
    db.add(roadmap_record)

    # Save to Saved Reports
    report = SavedReportModel(
        user_id=user.id,
        report_type="roadmap",
        title=f"Career Roadmap — {payload.career_goal}",
        summary=f"{payload.duration_weeks}-week strategic plan for {payload.experience_level} transitioning to {payload.career_goal}.",
        score=roadmap_data.progress_percent,
        tags=["Roadmap", f"{payload.duration_weeks}w", payload.experience_level],
        data={
            "roadmap": roadmap_data.model_dump(),
            "provider": provider,
            "model": model,
        },
    )
    db.add(report)

    # Keep the candidate profile aligned with the career goal they selected.
    if profile:
        profile.target_role = payload.career_goal

    db.commit()
    db.refresh(roadmap_record)

    return RoadmapOut.model_validate(roadmap_record)


@router.get("/latest", response_model=Optional[RoadmapOut])
def get_latest_roadmap(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    roadmap = (
        db.query(RoadmapModel)
        .filter(RoadmapModel.user_id == user.id)
        .order_by(RoadmapModel.created_at.desc())
        .first()
    )
    if not roadmap:
        return None

    return RoadmapOut.model_validate(roadmap)


@router.get("", response_model=List[RoadmapOut])
def list_roadmaps(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    roadmaps = (
        db.query(RoadmapModel)
        .filter(RoadmapModel.user_id == user.id)
        .order_by(RoadmapModel.created_at.desc())
        .all()
    )
    return [RoadmapOut.model_validate(r) for r in roadmaps]


@router.put("/{roadmap_id}/milestone", response_model=RoadmapOut)
def toggle_milestone(
    roadmap_id: str,
    payload: MilestoneToggleRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    roadmap = (
        db.query(RoadmapModel)
        .filter(RoadmapModel.id == roadmap_id, RoadmapModel.user_id == user.id)
        .first()
    )
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found.")

    milestones = [dict(milestone) for milestone in roadmap.milestones or []]
    updated = False
    for m in milestones:
        if m.get("week") == payload.week:
            m["completed"] = payload.completed
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail=f"Milestone week {payload.week} not found.")

    # Recalculate progress percent
    completed_count = sum(1 for m in milestones if m.get("completed"))
    total_count = len(milestones) if milestones else 1
    progress = int((completed_count / total_count) * 100)

    roadmap.milestones = milestones
    roadmap.progress_percent = progress
    db.commit()
    db.refresh(roadmap)

    return RoadmapOut.model_validate(roadmap)
