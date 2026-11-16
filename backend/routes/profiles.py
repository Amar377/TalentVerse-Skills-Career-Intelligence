"""Candidate Profile management routes."""
import json
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db, User, CandidateProfileModel
from backend.schemas import (
    CandidateProfileOut,
    CandidateProfileUpdate,
    ResumeAnalysisDetails,
)
from backend.auth_utils import get_current_user

router = APIRouter(prefix="/profiles", tags=["Candidate Profiles"])
logger = logging.getLogger(__name__)


def _profile_response(profile: CandidateProfileModel) -> CandidateProfileOut:
    response = CandidateProfileOut.model_validate(profile)
    analysis = ResumeAnalysisDetails.model_validate(profile.resume_analysis or {})
    response_data = response.model_dump()
    response_data.update(analysis.model_dump())
    response_data["resume_analysis"] = analysis.model_dump()
    return CandidateProfileOut.model_validate(response_data)


def _has_analysis_value(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


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
    return _profile_response(profile)


@router.put("/me", response_model=CandidateProfileOut)
def update_my_profile(
    payload: CandidateProfileUpdate,
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

    profile_fields = {
        "full_name",
        "email",
        "phone",
        "location",
        "target_role",
        "experience_level",
        "summary",
        "skills",
        "soft_skills",
        "experience",
        "education",
        "certifications",
        "projects",
        "missing_information",
        "strengths",
        "improvement_recommendations",
    }
    for field in profile_fields & payload.model_fields_set:
        setattr(profile, field, getattr(payload, field))

    if "resume_analysis" in payload.model_fields_set and payload.resume_analysis is not None:
        provided_analysis = payload.resume_analysis.model_dump(
            mode="json",
            exclude_unset=True,
        )
        if payload.replace_resume_analysis:
            profile.resume_analysis = provided_analysis
        else:
            current_analysis = dict(profile.resume_analysis or {})
            for field, value in provided_analysis.items():
                if _has_analysis_value(value):
                    current_analysis[field] = value
            profile.resume_analysis = current_analysis

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
    return _profile_response(profile)


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
    return [_profile_response(profile) for profile in profiles]
