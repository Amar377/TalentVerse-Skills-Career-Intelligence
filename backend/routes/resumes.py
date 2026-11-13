"""Resume upload, parsing, AI analysis, and profile extraction routes."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
import logging
from sqlalchemy.orm import Session
from datetime import datetime
from datetime import timedelta

from backend.database import get_db, User, ResumeRecordModel, CandidateProfileModel, SavedReportModel
from backend.schemas import (
    ResumeAnalysisRequest,
    ResumeAnalysisResponse,
    CandidateProfileData,
    CandidateProfileOut,
)
from backend.auth_utils import get_current_user
from backend.file_parser import parse_resume_file
from backend.ai_engine import analyze_resume_ai

from typing import Optional

router = APIRouter(prefix="/resumes", tags=["Resumes"])
logger = logging.getLogger(__name__)


def _recent_duplicate_resume(db: Session, user_id: str, raw_text: str):
    """Reuse a just-created analysis when the same request is retried rapidly."""
    return (
        db.query(ResumeRecordModel)
        .filter(
            ResumeRecordModel.user_id == user_id,
            ResumeRecordModel.raw_text == raw_text,
            ResumeRecordModel.created_at >= datetime.utcnow() - timedelta(seconds=90),
        )
        .order_by(ResumeRecordModel.created_at.desc())
        .first()
    )


def _response_for_record(record: ResumeRecordModel):
    return ResumeAnalysisResponse(
        profile=CandidateProfileData.model_validate(record.parsed_profile),
        raw_text=record.raw_text,
        extracted_at=record.created_at,
    )


def _report_summary(text: str) -> str | None:
    summary = text.strip()
    if not summary:
        return None
    return summary[:200].rstrip() + ("…" if len(summary) > 200 else "")


@router.post("/upload", response_model=ResumeAnalysisResponse)
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A resume filename is required.")

    contents = await file.read(10 * 1024 * 1024 + 1)
    if len(contents) > 10 * 1024 * 1024:  # Read at most one byte beyond the 10MB limit.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum allowed limit of 10MB.",
        )

    try:
        extracted_text, file_type = parse_resume_file(file.filename, contents)
    except Exception as exc:
        logger.warning("Resume parsing failed (%s).", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not parse this resume. Check that the file is valid and try again.",
        )

    if len(extracted_text.strip()) < 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract enough readable text from the file. Please paste your resume text directly.",
        )

    duplicate = _recent_duplicate_resume(db, user.id, extracted_text)
    if duplicate:
        return _response_for_record(duplicate)

    # Run AI Analysis
    profile_data, provider, model = analyze_resume_ai(extracted_text, session_id=user.id)

    # Save Resume Record
    record = ResumeRecordModel(
        user_id=user.id,
        filename=file.filename,
        file_type=file_type,
        raw_text=extracted_text,
        parsed_profile=profile_data.model_dump(),
    )
    db.add(record)

    # Update or Create User's Active Profile
    profile = db.query(CandidateProfileModel).filter(CandidateProfileModel.user_id == user.id).order_by(CandidateProfileModel.updated_at.desc()).first()
    if not profile:
        profile = CandidateProfileModel(user_id=user.id)
        db.add(profile)

    for field, val in profile_data.model_dump().items():
        if hasattr(profile, field) and val is not None:
            setattr(profile, field, val)

    # Create Saved Report
    report = SavedReportModel(
        user_id=user.id,
        report_type="resume",
        title=f"Resume Analysis — {file.filename}",
        summary=_report_summary(profile_data.summary),
        score=profile_data.readiness_score,
        tags=["Resume", file_type.upper(), profile_data.target_role or "General"],
        data={
            "profile": profile_data.model_dump(),
            "filename": file.filename,
            "provider": provider,
            "model": model,
        },
    )
    db.add(report)
    db.commit()

    return ResumeAnalysisResponse(
        profile=profile_data,
        raw_text=extracted_text,
        provider_used=provider,
        model_used=model,
    )


@router.post("/analyze-text", response_model=ResumeAnalysisResponse)
def analyze_text(
    payload: ResumeAnalysisRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    duplicate = _recent_duplicate_resume(db, user.id, payload.resume_text)
    if duplicate:
        return _response_for_record(duplicate)

    profile_data, provider, model = analyze_resume_ai(payload.resume_text, session_id=user.id)

    # Save record
    record = ResumeRecordModel(
        user_id=user.id,
        filename="pasted_text_resume.txt",
        file_type="text",
        raw_text=payload.resume_text,
        parsed_profile=profile_data.model_dump(),
    )
    db.add(record)

    # Update Profile
    profile = db.query(CandidateProfileModel).filter(CandidateProfileModel.user_id == user.id).order_by(CandidateProfileModel.updated_at.desc()).first()
    if not profile:
        profile = CandidateProfileModel(user_id=user.id)
        db.add(profile)

    for field, val in profile_data.model_dump().items():
        if hasattr(profile, field) and val is not None:
            setattr(profile, field, val)

    # Create Saved Report
    report = SavedReportModel(
        user_id=user.id,
        report_type="resume",
        title="Resume Analysis — Text Input",
        summary=_report_summary(profile_data.summary),
        score=profile_data.readiness_score,
        tags=["Resume", "Text Input", profile_data.target_role or "General"],
        data={
            "profile": profile_data.model_dump(),
            "filename": "pasted_text_resume.txt",
            "provider": provider,
            "model": model,
        },
    )
    db.add(report)
    db.commit()

    return ResumeAnalysisResponse(
        profile=profile_data,
        raw_text=payload.resume_text,
        provider_used=provider,
        model_used=model,
    )


@router.get("/latest", response_model=Optional[ResumeAnalysisResponse])
def get_latest_resume(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = (
        db.query(ResumeRecordModel)
        .filter(ResumeRecordModel.user_id == user.id)
        .order_by(ResumeRecordModel.created_at.desc())
        .first()
    )
    if not record:
        return None

    return ResumeAnalysisResponse(
        profile=CandidateProfileData.model_validate(record.parsed_profile),
        raw_text=record.raw_text,
        extracted_at=record.created_at,
    )
