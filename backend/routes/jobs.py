"""Job Matcher routes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db, User, JobMatchModel, SavedReportModel, CandidateProfileModel
from backend.schemas import (
    JobMatchRequest,
    JobMatchOut,
    CandidateProfileData,
)
from backend.auth_utils import get_current_user
from backend.ai_engine import match_job_ai

router = APIRouter(prefix="/jobs", tags=["Job Matcher"])


@router.post("/match", response_model=JobMatchOut)
def match_job_endpoint(
    payload: JobMatchRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Determine which profile to compare against
    profile_data = payload.custom_profile
    if not profile_data:
        profile_model = None
        if payload.profile_id:
            profile_model = db.query(CandidateProfileModel).filter(
                CandidateProfileModel.id == payload.profile_id,
                CandidateProfileModel.user_id == user.id,
            ).first()
            if not profile_model:
                raise HTTPException(status_code=404, detail="Candidate profile not found.")
        else:
            profile_model = (
                db.query(CandidateProfileModel)
                .filter(CandidateProfileModel.user_id == user.id)
                .order_by(CandidateProfileModel.updated_at.desc(), CandidateProfileModel.created_at.desc())
                .first()
            )

        if profile_model:
            profile_data = CandidateProfileData(
                full_name=profile_model.full_name,
                email=profile_model.email,
                phone=profile_model.phone,
                location=profile_model.location,
                target_role=profile_model.target_role,
                experience_level=profile_model.experience_level or "Entry-level",
                summary=profile_model.summary or "",
                skills=profile_model.skills or [],
                soft_skills=profile_model.soft_skills or [],
                experience=profile_model.experience or [],
                education=profile_model.education or [],
                certifications=profile_model.certifications or [],
                projects=profile_model.projects or [],
                missing_information=profile_model.missing_information or [],
                strengths=profile_model.strengths or [],
                improvement_recommendations=profile_model.improvement_recommendations or [],
                readiness_score=profile_model.readiness_score if profile_model.readiness_score is not None else 0,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Create or upload a candidate profile before running a job match.",
            )

    target_role = payload.target_role or profile_data.target_role or "Software Engineer"
    match_result, provider, model = match_job_ai(
        profile=profile_data,
        job_description=payload.job_description,
        target_role=target_role,
        session_id=user.id,
        preferred_provider=payload.preferred_provider,
    )

    match_record = JobMatchModel(
        user_id=user.id,
        target_role=target_role,
        company=payload.company or "Hiring Company",
        job_description=payload.job_description,
        match_score_percent=match_result.match_score_percent,
        matching_skills=match_result.matching_skills,
        missing_or_unverified_skills=match_result.missing_or_unverified_skills,
        experience_relevance=match_result.experience_relevance,
        education_relevance=match_result.education_relevance,
        strengths=match_result.strengths,
        evidence=match_result.evidence,
        improvement_actions=match_result.improvement_actions,
        caveat=match_result.caveat,
    )
    db.add(match_record)

    # Save to Saved Reports
    report = SavedReportModel(
        user_id=user.id,
        report_type="job_match",
        title=f"Job Match — {target_role} ({payload.company or 'Target Role'})",
        summary=f"Fit score {match_result.match_score_percent}% for {target_role}. Identified {len(match_result.matching_skills)} matching skills and {len(match_result.missing_or_unverified_skills)} gap areas.",
        score=match_result.match_score_percent,
        tags=["Job Match", f"{match_result.match_score_percent}% Fit", target_role],
        data={
            "job_match": match_result.model_dump(),
            "target_role": target_role,
            "company": payload.company,
            "provider": provider,
            "model": model,
        },
    )
    db.add(report)
    db.commit()
    db.refresh(match_record)

    return JobMatchOut.model_validate(match_record)


@router.get("/latest", response_model=JobMatchOut)
def get_latest_job_match(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    match = (
        db.query(JobMatchModel)
        .filter(JobMatchModel.user_id == user.id)
        .order_by(JobMatchModel.created_at.desc())
        .first()
    )
    if not match:
        raise HTTPException(status_code=404, detail="No job match analyses found.")
    return JobMatchOut.model_validate(match)


@router.get("", response_model=List[JobMatchOut])
def list_job_matches(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    matches = (
        db.query(JobMatchModel)
        .filter(JobMatchModel.user_id == user.id)
        .order_by(JobMatchModel.created_at.desc())
        .all()
    )
    return [JobMatchOut.model_validate(m) for m in matches]
