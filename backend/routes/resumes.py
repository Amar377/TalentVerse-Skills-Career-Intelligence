"""Resume upload, parsing, AI analysis, and profile extraction routes."""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
import logging
from pydantic import ValidationError
from sqlalchemy.orm import Session
from datetime import datetime
from datetime import timedelta

from backend.database import get_db, User, ResumeRecordModel, CandidateProfileModel, SavedReportModel
from backend.file_parser import SUPPORTED_RESUME_FORMATS, parse_resume_file
from backend.schemas import (
    AIProviderName,
    ResumeAnalysisRequest,
    ResumeAnalysisResponse,
    CandidateProfileData,
    ResumeAnalysisDetails,
    ResumeAnalysisProfile,
)
from backend.auth_utils import get_current_user
from backend.ai_engine import (
    RESUME_REQUIRED_FIELDS,
    analyze_resume_ai,
    resume_analysis_issues,
)

from typing import Optional

router = APIRouter(prefix="/resumes", tags=["Resumes"])
logger = logging.getLogger(__name__)


def _recent_duplicate_resume(db: Session, user_id: str, raw_text: str):
    """Reuse a just-created analysis when the same request is retried rapidly."""
    record = (
        db.query(ResumeRecordModel)
        .filter(
            ResumeRecordModel.user_id == user_id,
            ResumeRecordModel.raw_text == raw_text,
            ResumeRecordModel.created_at >= datetime.utcnow() - timedelta(seconds=90),
        )
        .order_by(ResumeRecordModel.created_at.desc())
        .first()
    )
    if record and not _is_complete_resume_snapshot(record.parsed_profile or {}):
        logger.info("Skipping reuse of an incomplete cached resume analysis.")
        return None
    return record


def _is_complete_resume_snapshot(profile_snapshot: dict) -> bool:
    provided_fields = set(profile_snapshot.get("_provided_fields") or ())
    if not RESUME_REQUIRED_FIELDS.issubset(provided_fields):
        return False
    try:
        profile = CandidateProfileData.model_validate(profile_snapshot)
    except ValidationError:
        return False
    return not resume_analysis_issues(profile)


def _response_for_record(record: ResumeRecordModel):
    profile_snapshot = record.parsed_profile or {}
    if not _is_complete_resume_snapshot(profile_snapshot):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The saved resume analysis is incomplete. Re-upload the resume to generate "
                "a complete analysis; no new result was saved."
            ),
        )
    profile_data = CandidateProfileData.model_validate(profile_snapshot)
    return ResumeAnalysisResponse(
        profile=_analysis_response_profile(profile_data),
        raw_text=record.raw_text,
        extracted_at=record.created_at,
        provider_used=profile_snapshot.get("_provider_used"),
        model_used=profile_snapshot.get("_model_used"),
    )


def _analysis_response_profile(profile: CandidateProfileData) -> ResumeAnalysisProfile:
    analysis_fields = set(ResumeAnalysisDetails.model_fields)
    profile_values = profile.model_dump(mode="json")
    profile_values["resume_analysis"] = profile.model_dump(
        include=analysis_fields,
        mode="json",
    )
    return ResumeAnalysisProfile.model_validate(profile_values)


def _merge_candidate_profile(
    db: Session,
    user: User,
    extracted: CandidateProfileData,
    replace_existing: bool = False,
    provided_fields: Optional[set[str]] = None,
) -> CandidateProfileModel:
    profile = (
        db.query(CandidateProfileModel)
        .filter(CandidateProfileModel.user_id == user.id)
        .order_by(CandidateProfileModel.updated_at.desc(), CandidateProfileModel.created_at.desc())
        .first()
    )
    if not profile:
        profile = CandidateProfileModel(user_id=user.id)
        db.add(profile)

    extracted_fields = provided_fields if provided_fields is not None else extracted.model_fields_set
    scalar_fields = (
        "full_name",
        "email",
        "phone",
        "location",
        "target_role",
        "experience_level",
        "summary",
        "readiness_score",
    )
    list_fields = (
        "skills",
        "soft_skills",
        "experience",
        "education",
        "certifications",
        "projects",
        "missing_information",
        "strengths",
        "improvement_recommendations",
    )

    for field in scalar_fields:
        value = getattr(extracted, field)
        if (
            field not in extracted_fields
            or value is None
            or (isinstance(value, str) and not value.strip())
        ):
            continue
        current = getattr(profile, field)
        if (
            replace_existing
            or current is None
            or (isinstance(current, str) and not current.strip())
        ):
            setattr(profile, field, value)

    for field in list_fields:
        if field not in extracted_fields:
            continue
        new_values = [
            value for value in (getattr(extracted, field) or [])
            if isinstance(value, str) and value.strip()
        ]
        if not new_values:
            continue
        current_values = getattr(profile, field) or []
        if replace_existing:
            setattr(profile, field, new_values)
            continue

        merged = list(current_values)
        seen = {value.strip().casefold() for value in merged if isinstance(value, str)}
        for value in new_values:
            key = value.strip().casefold()
            if key not in seen:
                merged.append(value)
                seen.add(key)
        setattr(profile, field, merged)

    analysis_fields = set(ResumeAnalysisDetails.model_fields)
    provided_analysis_fields = extracted_fields & analysis_fields
    if provided_analysis_fields:
        analysis_updates = extracted.model_dump(
            include=provided_analysis_fields,
            mode="json",
        )
        current_analysis = dict(profile.resume_analysis or {})
        for field, value in analysis_updates.items():
            if replace_existing or _has_analysis_value(value):
                current_analysis[field] = value
        profile.resume_analysis = current_analysis

    return profile


def _has_analysis_value(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _report_summary(text: str) -> str | None:
    summary = text.strip()
    if not summary:
        return None
    return summary[:200].rstrip() + ("…" if len(summary) > 200 else "")


@router.post("/upload", response_model=ResumeAnalysisResponse)
async def upload_resume(
    file: UploadFile = File(...),
    preferred_provider: Optional[AIProviderName] = Form(default=None),
    replace_profile: bool = Form(default=False),
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
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ImportError as exc:
        logger.exception("Resume parser dependency is unavailable.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Resume parsing is not available because a required parser package is missing. "
                f"Install backend requirements to enable {SUPPORTED_RESUME_FORMATS} uploads."
            ),
        ) from exc

    if len(extracted_text.strip()) < 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Could not extract enough readable text. This can happen with scanned/image-only PDFs, "
                "which need OCR, or with an empty document. Please use a text-based PDF, DOCX, TXT, "
                "or Markdown file, or paste your resume text directly."
            ),
        )

    duplicate = _recent_duplicate_resume(db, user.id, extracted_text)
    if duplicate:
        duplicate_profile = duplicate.parsed_profile or {}
        _merge_candidate_profile(
            db,
            user,
            CandidateProfileData.model_validate(duplicate_profile),
            replace_existing=replace_profile,
            provided_fields=(
                set(duplicate_profile["_provided_fields"])
                if "_provided_fields" in duplicate_profile
                else None
            ),
        )
        db.commit()
        return _response_for_record(duplicate)

    # Run AI Analysis
    profile_data, provider, model = analyze_resume_ai(
        extracted_text,
        session_id=user.id,
        preferred_provider=preferred_provider,
    )
    if not profile_data.full_name:
        profile_data.full_name = user.full_name
    if not profile_data.email:
        profile_data.email = user.email

    # Save Resume Record
    profile_snapshot = profile_data.model_dump()
    profile_snapshot["_provider_used"] = provider
    profile_snapshot["_model_used"] = model
    profile_snapshot["_provided_fields"] = sorted(profile_data.model_fields_set)
    record = ResumeRecordModel(
        user_id=user.id,
        filename=file.filename,
        file_type=file_type,
        raw_text=extracted_text,
        parsed_profile=profile_snapshot,
    )
    db.add(record)

    _merge_candidate_profile(db, user, profile_data, replace_existing=replace_profile)

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
        profile=_analysis_response_profile(profile_data),
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
        duplicate_profile = duplicate.parsed_profile or {}
        _merge_candidate_profile(
            db,
            user,
            CandidateProfileData.model_validate(duplicate_profile),
            replace_existing=payload.replace_profile,
            provided_fields=(
                set(duplicate_profile["_provided_fields"])
                if "_provided_fields" in duplicate_profile
                else None
            ),
        )
        db.commit()
        return _response_for_record(duplicate)

    profile_data, provider, model = analyze_resume_ai(
        payload.resume_text,
        session_id=user.id,
        preferred_provider=payload.preferred_provider,
    )
    if not profile_data.full_name:
        profile_data.full_name = user.full_name
    if not profile_data.email:
        profile_data.email = user.email

    # Save record
    profile_snapshot = profile_data.model_dump()
    profile_snapshot["_provider_used"] = provider
    profile_snapshot["_model_used"] = model
    profile_snapshot["_provided_fields"] = sorted(profile_data.model_fields_set)
    record = ResumeRecordModel(
        user_id=user.id,
        filename="pasted_text_resume.txt",
        file_type="text",
        raw_text=payload.resume_text,
        parsed_profile=profile_snapshot,
    )
    db.add(record)

    _merge_candidate_profile(db, user, profile_data, replace_existing=payload.replace_profile)

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
        profile=_analysis_response_profile(profile_data),
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

    return _response_for_record(record)
