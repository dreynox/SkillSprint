import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import ContestParticipation, ContestSubmission, QuizSubmission, User
from schemas import MessageResponse, UserOut, UserProfileUpdate, UserStatsOut
from typing import List

router = APIRouter()

MAX_AVATAR_BYTES = 5 * 1024 * 1024
UPLOADS_DIR = Path(__file__).resolve().parents[1] / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/me/avatar", response_model=UserOut)
async def upload_my_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image uploads are allowed.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(content) > MAX_AVATAR_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image too large. Max allowed size is 5MB.",
        )

    original_ext = os.path.splitext(file.filename or "")[1].lower()
    if original_ext not in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}:
        original_ext = ".png"

    filename = f"avatar_{current_user.id}_{uuid4().hex}{original_ext}"
    destination = UPLOADS_DIR / filename
    destination.write_bytes(content)

    # Keep URL backend-relative so frontend can combine it with API base.
    current_user.avatar_url = f"/uploads/{filename}"
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


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


@router.delete("/me", response_model=MessageResponse)
def delete_my_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Remove dependent rows first to avoid foreign key violations.
    db.query(ContestParticipation).filter(ContestParticipation.user_id == current_user.id).delete(
        synchronize_session=False
    )
    db.query(ContestSubmission).filter(ContestSubmission.user_id == current_user.id).delete(
        synchronize_session=False
    )
    db.query(QuizSubmission).filter(QuizSubmission.user_id == current_user.id).delete(
        synchronize_session=False
    )

    if current_user.avatar_url and current_user.avatar_url.startswith("/uploads/"):
        avatar_path = Path(__file__).resolve().parents[1] / current_user.avatar_url.lstrip("/")
        if avatar_path.exists() and avatar_path.is_file():
            avatar_path.unlink(missing_ok=True)

    db.delete(current_user)
    db.commit()

    return {"message": "Account deleted successfully."}


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


@router.get("", response_model=List[UserOut])
def list_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all users for messaging"""
    users = db.query(User).all()
    return users
