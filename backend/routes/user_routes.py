from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import ContestParticipation, ContestSubmission, QuizSubmission, User
from schemas import UserOut, UserProfileUpdate, UserStatsOut

router = APIRouter()


@router.get("/me", response_model=UserOut)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
def update_my_profile(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(current_user, key, value)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/stats", response_model=UserStatsOut)
def get_my_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contests_joined = (
        db.query(func.count(ContestParticipation.id))
        .filter(ContestParticipation.user_id == current_user.id)
        .scalar()
        or 0
    )

    contest_submissions = (
        db.query(func.count(ContestSubmission.id))
        .filter(ContestSubmission.user_id == current_user.id)
        .scalar()
        or 0
    )

    quiz_attempts = (
        db.query(func.count(QuizSubmission.id))
        .filter(QuizSubmission.user_id == current_user.id)
        .scalar()
        or 0
    )

    quiz_score_sum = (
        db.query(func.coalesce(func.sum(QuizSubmission.score), 0))
        .filter(QuizSubmission.user_id == current_user.id)
        .scalar()
        or 0
    )

    quiz_questions_sum = (
        db.query(func.coalesce(func.sum(QuizSubmission.total_questions), 0))
        .filter(QuizSubmission.user_id == current_user.id)
        .scalar()
        or 0
    )

    return UserStatsOut(
        contests_joined=int(contests_joined),
        contest_submissions=int(contest_submissions),
        quiz_attempts=int(quiz_attempts),
        total_quiz_score=int(quiz_score_sum),
        quiz_questions_attempted=int(quiz_questions_sum),
    )
