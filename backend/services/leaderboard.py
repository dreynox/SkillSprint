import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from redis_client import get_redis_client
from models import User, QuizSubmission, ContestSubmission, ContestParticipation
from database import SessionLocal

LEADERBOARD_KEY = "leaderboard:xp"
USER_DETAILS_PREFIX = "user_details:"

def get_badge_for_points(points: int) -> str:
    if points >= 1000:
        return "Diamond"
    elif points >= 500:
        return "Platinum"
    elif points >= 200:
        return "Gold"
    elif points >= 100:
        return "Silver"
    else:
        return "Bronze"

def update_user_leaderboard_cache(user_id: int) -> None:
    """
    Recalculates a single user's total points and stats, then updates Redis.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return

        quiz_stats = (
            db.query(
                func.count(QuizSubmission.id).label("quiz_attempts"),
                func.coalesce(func.sum(QuizSubmission.score), 0).label("quiz_score"),
            )
            .filter(QuizSubmission.user_id == user_id)
            .first()
        )

        contest_subs = db.query(func.count(ContestSubmission.id)).filter(ContestSubmission.user_id == user_id).scalar() or 0
        contests_joined = db.query(func.count(ContestParticipation.id)).filter(ContestParticipation.user_id == user_id).scalar() or 0
        
        quiz_attempts = int(quiz_stats.quiz_attempts) if quiz_stats else 0
        quiz_score = int(quiz_stats.quiz_score) if quiz_stats else 0
        
        total_points = (
            quiz_score * 10
            + quiz_attempts * 5
            + contests_joined * 15
            + contest_subs * 20
            + (user.extra_xp or 0)
        )

        redis_db = get_redis_client()
        with redis_db.lock(f"lock:leaderboard:{user_id}", timeout=10, blocking_timeout=10):
            pipe = redis_db.pipeline()
            if total_points > 0:
                pipe.zadd(LEADERBOARD_KEY, {str(user_id): total_points})
                
                user_data = {
                    "id": user.id,
                    "name": user.name,
                    "avatar_url": user.avatar_url,
                    "branch": user.branch,
                    "year": user.year,
                    "domain": user.domain,
                    "subject": user.subject,
                    "quiz_attempts": quiz_attempts,
                    "quiz_score": quiz_score,
                    "contests_joined": contests_joined,
                    "contest_submissions": contest_subs,
                    "total_points": total_points,
                    "badge": get_badge_for_points(total_points)
                }
                pipe.set(f"{USER_DETAILS_PREFIX}{user_id}", json.dumps(user_data))
            else:
                pipe.zrem(LEADERBOARD_KEY, str(user_id))
                pipe.delete(f"{USER_DETAILS_PREFIX}{user_id}")
            pipe.execute()
    except Exception as e:
        print(f"Error updating Redis leaderboard cache: {e}")
    finally:
        db.close()


def get_top_users_from_redis(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieves the top users from the Redis sorted set using ZREVRANGE, completely bypassing the DB.
    """
    try:
        redis_db = get_redis_client()
        top_user_ids = redis_db.zrevrange(LEADERBOARD_KEY, 0, limit - 1)
        
        leaderboard = []
        rank = 1
        for uid in top_user_ids:
            uid_str = uid if isinstance(uid, str) else uid.decode('utf-8')
            user_data_json = redis_db.get(f"{USER_DETAILS_PREFIX}{uid_str}")
            if user_data_json:
                user_data = json.loads(user_data_json)
                user_data["rank"] = rank
                leaderboard.append(user_data)
                rank += 1
        return leaderboard
    except Exception as e:
        print(f"Error fetching leaderboard from Redis: {e}")
        return []

def is_leaderboard_cache_ready() -> bool:
    try:
        redis_db = get_redis_client()
        return bool(redis_db.get("leaderboard:ready"))
    except Exception:
        return False

def rebuild_full_leaderboard_cache() -> None:
    db = SessionLocal()
    try:
        redis_db = get_redis_client()
        with redis_db.lock("lock:leaderboard_rebuild", timeout=60, blocking_timeout=5):
            if redis_db.get("leaderboard:ready"):
                return
                
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
                .all()
            )

            pipe = redis_db.pipeline()
            for row in rows:
                points = int(row.total_points or 0)
                pipe.zadd(LEADERBOARD_KEY, {str(row.id): points})
                user_data = {
                    "id": row.id,
                    "name": row.name,
                    "avatar_url": row.avatar_url,
                    "branch": row.branch,
                    "year": row.year,
                    "domain": row.domain,
                    "subject": row.subject,
                    "quiz_attempts": int(row.quiz_attempts or 0),
                    "quiz_score": int(row.quiz_score or 0),
                    "contests_joined": int(row.contests_joined or 0),
                    "contest_submissions": int(row.contest_submissions or 0),
                    "total_points": points,
                    "badge": get_badge_for_points(points)
                }
                pipe.set(f"{USER_DETAILS_PREFIX}{row.id}", json.dumps(user_data))
            
            pipe.set("leaderboard:ready", "1")
            pipe.execute()
    except Exception as e:
        print(f"Error rebuilding Redis leaderboard cache: {e}")
    finally:
        db.close()
