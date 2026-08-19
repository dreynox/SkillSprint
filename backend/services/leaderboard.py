import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from redis_client import get_redis_client
from models import User, QuizSubmission, ContestSubmission, ContestParticipation

LEADERBOARD_KEY = "leaderboard:xp"
USER_DETAILS_PREFIX = "user_details:"

def _badge_for_points(points: int) -> str:
    # We can copy the logic from user_routes or just assume it is available.
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

def update_user_leaderboard_cache(user_id: int, db: Session) -> None:
    """
    Recalculates a single user's total points and stats, then updates Redis.
    """
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
        if total_points > 0:
            redis_db.zadd(LEADERBOARD_KEY, {str(user_id): total_points})
            
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
                "badge": _badge_for_points(total_points)
            }
            redis_db.set(f"{USER_DETAILS_PREFIX}{user_id}", json.dumps(user_data))
        else:
            redis_db.zrem(LEADERBOARD_KEY, str(user_id))
            redis_db.delete(f"{USER_DETAILS_PREFIX}{user_id}")
            
    except Exception as e:
        print(f"Error updating Redis leaderboard cache: {e}")


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
