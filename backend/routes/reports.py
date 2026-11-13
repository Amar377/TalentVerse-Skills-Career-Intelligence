"""Saved Reports management routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db, User, SavedReportModel
from backend.schemas import SavedReportCreate, SavedReportOut
from backend.auth_utils import get_current_user

router = APIRouter(prefix="/reports", tags=["Saved Reports"])


@router.get("", response_model=List[SavedReportOut])
def list_reports(
    report_type: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(SavedReportModel).filter(SavedReportModel.user_id == user.id)
    if report_type:
        query = query.filter(SavedReportModel.report_type == report_type)
    reports = query.order_by(SavedReportModel.created_at.desc()).all()
    return [SavedReportOut.model_validate(r) for r in reports]


@router.post("", response_model=SavedReportOut)
def create_report(
    payload: SavedReportCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = SavedReportModel(
        user_id=user.id,
        report_type=payload.report_type,
        title=payload.title,
        summary=payload.summary,
        score=payload.score,
        tags=payload.tags,
        data=payload.data,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return SavedReportOut.model_validate(report)


@router.get("/{report_id}", response_model=SavedReportOut)
def get_report(
    report_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = (
        db.query(SavedReportModel)
        .filter(SavedReportModel.id == report_id, SavedReportModel.user_id == user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    return SavedReportOut.model_validate(report)


@router.delete("/{report_id}")
def delete_report(
    report_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = (
        db.query(SavedReportModel)
        .filter(SavedReportModel.id == report_id, SavedReportModel.user_id == user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    db.delete(report)
    db.commit()
    return {"status": "success", "message": "Report deleted successfully."}
