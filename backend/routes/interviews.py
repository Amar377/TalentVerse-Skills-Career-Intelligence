"""Interview Coach routes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db, User, InterviewModel, SavedReportModel, CandidateProfileModel
from backend.schemas import (
    InterviewQuestionRequest,
    InterviewQuestionsResponse,
    InterviewEvaluateRequest,
    InterviewOut,
)
from backend.auth_utils import get_current_user
from backend.ai_engine import (
    generate_interview_questions_ai,
    evaluate_interview_ai,
)

router = APIRouter(prefix="/interviews", tags=["Interview Coach"])


@router.post("/questions", response_model=InterviewQuestionsResponse)
def get_questions(
    payload: InterviewQuestionRequest,
    user: User = Depends(get_current_user),
):
    questions, provider, model = generate_interview_questions_ai(
        target_role=payload.target_role,
        interview_type=payload.interview_type,
        level=payload.level,
        session_id=user.id,
    )
    return InterviewQuestionsResponse(
        target_role=payload.target_role,
        questions=questions,
    )


@router.post("/evaluate", response_model=InterviewOut)
def evaluate_answer(
    payload: InterviewEvaluateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    evaluation, provider, model = evaluate_interview_ai(
        target_role=payload.target_role,
        interview_type=payload.interview_type,
        question=payload.question,
        user_answer=payload.user_answer,
        session_id=user.id,
    )

    record = InterviewModel(
        user_id=user.id,
        target_role=payload.target_role,
        interview_type=payload.interview_type,
        question=payload.question,
        user_answer=payload.user_answer,
        answer_score=evaluation.answer_score,
        feedback=evaluation.feedback,
        strengths=evaluation.strengths,
        improvement_areas=evaluation.improvement_areas,
        missing_concepts=evaluation.missing_concepts,
        suggested_answer=evaluation.suggested_answer,
        practice_tasks=evaluation.practice_tasks,
        next_session_focus=evaluation.next_session_focus,
    )
    db.add(record)

    # Save to Saved Reports
    report = SavedReportModel(
        user_id=user.id,
        report_type="interview",
        title=f"Interview Feedback — {payload.target_role} ({payload.interview_type.title()})",
        summary=f"Score: {evaluation.answer_score}/100. Evaluated {payload.interview_type} response regarding '{payload.question[:60]}...'.",
        score=evaluation.answer_score,
        tags=["Interview", f"{evaluation.answer_score} pts", payload.interview_type.title()],
        data={
            "interview": evaluation.model_dump(),
            "question": payload.question,
            "user_answer": payload.user_answer,
            "provider": provider,
            "model": model,
        },
    )
    db.add(report)
    db.commit()
    db.refresh(record)

    return InterviewOut.model_validate(record)


@router.get("/history", response_model=List[InterviewOut])
def get_interview_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = (
        db.query(InterviewModel)
        .filter(InterviewModel.user_id == user.id)
        .order_by(InterviewModel.created_at.desc())
        .all()
    )
    return [InterviewOut.model_validate(r) for r in records]
