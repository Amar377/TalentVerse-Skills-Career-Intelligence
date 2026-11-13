"""Candidate Profile management routes."""
import json
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db, User, CandidateProfileModel
from backend.schemas import CandidateProfileData, CandidateProfileOut
from backend.auth_utils import get_current_user

router = APIRouter(prefix="/profiles", tags=["Candidate Profiles"])
logger = logging.getLogger(__name__)


def _seed_profiles_if_needed(db: Session, user: User):
    """Create a profile for this user, importing only a legacy record with a matching email."""
    existing = (
        db.query(CandidateProfileModel)
        .filter(CandidateProfileModel.user_id == user.id)
        .order_by(CandidateProfileModel.updated_at.desc(), CandidateProfileModel.created_at.desc())
        .first()
    )
    if existing:
        return existing

    json_path = Path(__file__).resolve().parent.parent.parent / "talentverse_profiles.json"
    legacy_profile = None
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                legacy_profile = next(
                    (
                        item.get("profile")
                        for item in data
                        if isinstance(item, dict)
                        and isinstance(item.get("profile"), dict)
                        and str(item["profile"].get("email", "")).strip().casefold() == user.email.casefold()
                    ),
                    None,
                )
        except (OSError, json.JSONDecodeError):
            logger.warning("Legacy profile data could not be read; creating an empty profile.")

    profile_data = legacy_profile or {}
    profile = CandidateProfileModel(
        user_id=user.id,
        full_name=profile_data.get("full_name") or user.full_name,
        email=user.email,
        phone=profile_data.get("phone"),
        location=profile_data.get("location"),
        target_role=profile_data.get("target_role"),
        experience_level=profile_data.get("experience_level") or "Entry-level",
        summary=profile_data.get("summary") or "",
        skills=profile_data.get("skills") if isinstance(profile_data.get("skills"), list) else [],
        soft_skills=profile_data.get("soft_skills") if isinstance(profile_data.get("soft_skills"), list) else [],
        experience=profile_data.get("experience") if isinstance(profile_data.get("experience"), list) else [],
        education=profile_data.get("education") if isinstance(profile_data.get("education"), list) else [],
        certifications=profile_data.get("certifications") if isinstance(profile_data.get("certifications"), list) else [],
        projects=profile_data.get("projects") if isinstance(profile_data.get("projects"), list) else [],
        missing_information=profile_data.get("missing_information") if isinstance(profile_data.get("missing_information"), list) else [],
        strengths=profile_data.get("strengths") if isinstance(profile_data.get("strengths"), list) else [],
        improvement_recommendations=profile_data.get("improvement_recommendations") if isinstance(profile_data.get("improvement_recommendations"), list) else [],
        readiness_score=min(max(profile_data.get("readiness_score", 0), 0), 100)
        if isinstance(profile_data.get("readiness_score", 0), int)
        else 0,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/me", response_model=CandidateProfileOut)
def get_my_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = _seed_profiles_if_needed(db, user)
    return CandidateProfileOut.model_validate(profile)


@router.put("/me", response_model=CandidateProfileOut)
def update_my_profile(
    payload: CandidateProfileData,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(CandidateProfileModel)
        .filter(CandidateProfileModel.user_id == user.id)
        .order_by(CandidateProfileModel.updated_at.desc(), CandidateProfileModel.created_at.desc())
        .first()
    )
    if not profile:
        profile = CandidateProfileModel(user_id=user.id)
        db.add(profile)

    for field, val in payload.model_dump().items():
        if hasattr(profile, field):
            setattr(profile, field, val)

    # Recalculate readiness score dynamically based on filled sections
    score = 0
    if profile.summary and len(profile.summary) > 40:
        score += 20
    if profile.skills and len(profile.skills) >= 4:
        score += 25
    if profile.experience and len(profile.experience) >= 1:
        score += 25
    if profile.education and len(profile.education) >= 1:
        score += 15
    if profile.projects and len(profile.projects) >= 1:
        score += 15
    profile.readiness_score = min(100, score)

    db.commit()
    db.refresh(profile)
    return CandidateProfileOut.model_validate(profile)


@router.get("", response_model=List[CandidateProfileOut])
def list_profiles(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profiles = (
        db.query(CandidateProfileModel)
        .filter(CandidateProfileModel.user_id == user.id)
        .order_by(CandidateProfileModel.updated_at.desc(), CandidateProfileModel.created_at.desc())
        .all()
    )
    if not profiles:
        p = _seed_profiles_if_needed(db, user)
        profiles = [p]
    return [CandidateProfileOut.model_validate(p) for p in profiles]
