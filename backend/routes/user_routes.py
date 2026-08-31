import os
import base64
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status, BackgroundTasks
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import ContestParticipation, ContestSubmission, QuizSubmission, User, Follow, Contest, Hackathon, Message
from schemas import AddXPRequest, LeaderboardEntryOut, MessageResponse, UserOut, UserProfileUpdate, UserStatsOut, FollowOut, SearchResult
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

    mime_type = file.content_type or "image/png"
    if mime_type not in {"image/png", "image/jpeg", "image/gif", "image/webp", "image/svg+xml"}:
        mime_type = "image/png"

    encoded_image = base64.b64encode(content).decode("ascii")
    current_user.avatar_url = f"data:{mime_type};base64,{encoded_image}"
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


@router.post("/me/add-xp", response_model=UserOut)
def add_my_xp(
    payload: AddXPRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Award extra XP to the logged-in user (from Practice or Quiz)."""
    if payload.xp < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="XP must be a positive integer")
    current_user.extra_xp = (current_user.extra_xp or 0) + payload.xp
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    from services.leaderboard import update_user_leaderboard_cache
    background_tasks.add_task(update_user_leaderboard_cache, current_user.id)
    
    return current_user



from fastapi import BackgroundTasks

@router.get("/leaderboard", response_model=List[LeaderboardEntryOut])
def get_leaderboard(
    background_tasks: BackgroundTasks,
    limit: int = Query(50, ge=1, le=50),
    db: Session = Depends(get_db),
):
    from services.leaderboard import (
        get_top_users_from_redis,
        is_leaderboard_cache_ready,
        rebuild_full_leaderboard_cache,
        get_badge_for_points,
    )
    
    # Try fetching from Redis first
    if is_leaderboard_cache_ready():
        cached_leaderboard = get_top_users_from_redis(limit)
        if cached_leaderboard:
            return cached_leaderboard

    # Trigger background rebuild since it's not ready
    background_tasks.add_task(rebuild_full_leaderboard_cache)

    # Fallback to DB if Redis is empty or down
    quiz_stats = (
        db.query(
            QuizSubmission.user_id.label("user_id"),
            func.count(QuizSubmission.id).label("quiz_attempts"),
            func.coalesce(func.sum(QuizSubmission.score), 0).label("quiz_score"),
        )
        .group_by(QuizSubmission.user_id)
        .subquery()
    )

    contest_stats = (
        db.query(
            ContestSubmission.user_id.label("user_id"),
            func.count(ContestSubmission.id).label("contest_submissions"),
        )
        .group_by(ContestSubmission.user_id)
        .subquery()
    )

    participation_stats = (
        db.query(
            ContestParticipation.user_id.label("user_id"),
            func.count(ContestParticipation.id).label("contests_joined"),
        )
        .group_by(ContestParticipation.user_id)
        .subquery()
    )

    total_points = (
        func.coalesce(quiz_stats.c.quiz_score, 0) * 10
        + func.coalesce(quiz_stats.c.quiz_attempts, 0) * 5
        + func.coalesce(participation_stats.c.contests_joined, 0) * 15
        + func.coalesce(contest_stats.c.contest_submissions, 0) * 20
        + func.coalesce(User.extra_xp, 0)
    )

    rows = (
        db.query(
            User.id.label("id"),
            User.name.label("name"),
            User.avatar_url.label("avatar_url"),
            User.branch.label("branch"),
            User.year.label("year"),
            User.domain.label("domain"),
            User.subject.label("subject"),
            User.extra_xp.label("extra_xp"),
            func.coalesce(quiz_stats.c.quiz_attempts, 0).label("quiz_attempts"),
            func.coalesce(quiz_stats.c.quiz_score, 0).label("quiz_score"),
            func.coalesce(participation_stats.c.contests_joined, 0).label("contests_joined"),
            func.coalesce(contest_stats.c.contest_submissions, 0).label("contest_submissions"),
            total_points.label("total_points"),
        )
        .outerjoin(quiz_stats, quiz_stats.c.user_id == User.id)
        .outerjoin(contest_stats, contest_stats.c.user_id == User.id)
        .outerjoin(participation_stats, participation_stats.c.user_id == User.id)
        .filter(total_points > 0)
        .order_by(total_points.desc(), User.name.asc())
        .limit(limit)
        .all()
    )

    leaderboard = []
    for index, row in enumerate(rows, start=1):
        points = int(row.total_points or 0)
        leaderboard.append(
            LeaderboardEntryOut(
                id=row.id,
                name=row.name,
                avatar_url=row.avatar_url,
                branch=row.branch,
                year=row.year,
                domain=row.domain,
                subject=row.subject,
                quiz_attempts=int(row.quiz_attempts or 0),
                quiz_score=int(row.quiz_score or 0),
                contests_joined=int(row.contests_joined or 0),
                contest_submissions=int(row.contest_submissions or 0),
                total_points=points,
                badge=get_badge_for_points(points),
                rank=index,
            )
        )

    return leaderboard


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
    query_text = q.strip() if q else ""
    if len(query_text) < 2:
        return []

    search_terms = [term for term in query_text.split() if term]
    query_term = f"%{query_text}%"
    results = []
    
    # Search users
    user_filters = []
    for term in search_terms:
        term_pattern = f"%{term}%"
        user_filters.append(
            or_(
                User.name.ilike(term_pattern),
                User.email.ilike(term_pattern),
                User.srn.ilike(term_pattern),
                User.prn.ilike(term_pattern),
                User.branch.ilike(term_pattern),
                User.division.ilike(term_pattern),
                User.roll_no.ilike(term_pattern),
                User.domain.ilike(term_pattern),
                User.subject.ilike(term_pattern),
            )
        )

    users_query = db.query(User)
    if user_filters:
        for user_filter in user_filters:
            users_query = users_query.filter(user_filter)
    users = users_query.all()
    
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
