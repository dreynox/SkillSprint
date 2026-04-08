import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import ContestParticipation, ContestSubmission, QuizSubmission, User, Follow, Contest, Hackathon, Message
from schemas import MessageResponse, UserOut, UserProfileUpdate, UserStatsOut, FollowOut, SearchResult
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


@router.get("/search", response_model=List[SearchResult])
def search(
    q: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search for users, contests, and hackathons"""
    if not q or len(q.strip()) < 2:
        return []
    
    query_term = f"%{q}%"
    results = []
    
    # Search users
    users = db.query(User).filter(
        or_(
            User.name.ilike(query_term),
            User.email.ilike(query_term)
        )
    ).all()
    
    for user in users:
        results.append(SearchResult(
            type="user",
            id=user.id,
            name=user.name,
            email=user.email,
            avatar_url=user.avatar_url,
            bio=user.bio
        ))
    
    # Search contests
    contests = db.query(Contest).filter(
        or_(
            Contest.name.ilike(query_term),
            Contest.description.ilike(query_term)
        )
    ).all()
    
    for contest in contests:
        results.append(SearchResult(
            type="contest",
            id=contest.id,
            title=contest.name,
            description=contest.description,
            is_active=contest.is_active,
            start_time=contest.start_time,
            end_time=contest.end_time
        ))
    
    # Search hackathons
    hackathons = db.query(Hackathon).filter(
        or_(
            Hackathon.title.ilike(query_term),
            Hackathon.description.ilike(query_term)
        )
    ).all()
    
    for hackathon in hackathons:
        results.append(SearchResult(
            type="hackathon",
            id=hackathon.id,
            title=hackathon.title,
            description=hackathon.description,
            is_active=hackathon.is_active,
            start_time=hackathon.start_time,
            end_time=hackathon.end_time
        ))
    
    return results


@router.get("/{user_id}", response_model=UserOut)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a user's public profile by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    return user


@router.post("/{user_id}/follow", response_model=FollowOut)
def follow_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Follow a user"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot follow yourself."
        )
    
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    
    existing_follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id
    ).first()
    
    if existing_follow:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already following this user."
        )
    
    follow = Follow(follower_id=current_user.id, following_id=user_id)
    db.add(follow)
    db.commit()
    db.refresh(follow)
    return follow


@router.delete("/{user_id}/follow", response_model=MessageResponse)
def unfollow_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unfollow a user"""
    follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id
    ).first()
    
    if not follow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not following this user."
        )
    
    db.delete(follow)
    db.commit()
    return {"message": "Unfollowed successfully."}


@router.get("/me/following", response_model=List[UserOut])
def get_my_following(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of users that current user is following"""
    follows = db.query(Follow).filter(Follow.follower_id == current_user.id).all()
    following_ids = [follow.following_id for follow in follows]
    
    if not following_ids:
        return []
    
    users = db.query(User).filter(User.id.in_(following_ids)).all()
    return users


@router.get("/{user_id}/followers", response_model=List[UserOut])
def get_user_followers(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of followers for a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    
    follows = db.query(Follow).filter(Follow.following_id == user_id).all()
    follower_ids = [follow.follower_id for follow in follows]
    
    if not follower_ids:
        return []
    
    followers = db.query(User).filter(User.id.in_(follower_ids)).all()
    return followers


@router.get("/{user_id}/is-following")
def check_if_following(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if current user is following the specified user"""
    follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id
    ).first()
    
    return {"is_following": follow is not None}
