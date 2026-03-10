from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import User, Contest, ContestProblem, ContestSubmission
from ..schemas import (
    ContestCreate,
    ContestResponse,
    ProblemCreate,
    ProblemResponse,
    SubmissionCreate,
    SubmissionResponse,
    LeaderboardEntry,
)
from ..auth import get_current_user, require_admin

router = APIRouter()


# ========== CONTEST ENDPOINTS ==========

@router.get("/", response_model=List[ContestResponse])
def list_contests(db: Session = Depends(get_db)):
    """Get all contests (public endpoint)"""
    contests = db.query(Contest).all()
    return contests


@router.post("/", response_model=ContestResponse, status_code=status.HTTP_201_CREATED)
def create_contest(
    payload: ContestCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Create a new contest (admin only)"""
    contest = Contest(**payload.model_dump())
    db.add(contest)
    db.commit()
    db.refresh(contest)
    return contest


@router.get("/{contest_id}", response_model=ContestResponse)
def get_contest(contest_id: int, db: Session = Depends(get_db)):
    """Get contest details"""
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    return contest


# ========== PROBLEM ENDPOINTS ==========

@router.get("/{contest_id}/problems", response_model=List[ProblemResponse])
def list_problems(contest_id: int, db: Session = Depends(get_db)):
    """Get all problems in a contest"""
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    problems = db.query(ContestProblem).filter(
        ContestProblem.contest_id == contest_id
    ).all()
    return problems


@router.post(
    "/{contest_id}/problems",
    response_model=ProblemResponse,
    status_code=status.HTTP_201_CREATED
)
def add_problem(
    contest_id: int,
    payload: ProblemCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Add a problem to a contest (admin only)"""
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    problem = ContestProblem(
        contest_id=contest_id,
        **payload.model_dump()
    )
    db.add(problem)
    db.commit()
    db.refresh(problem)
    return problem


# ========== SUBMISSION ENDPOINTS ==========

@router.post("/{contest_id}/submit", response_model=SubmissionResponse)
def submit_solution(
    contest_id: int,
    payload: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a solution for a problem in a contest"""
    # Verify contest exists
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Verify problem exists and belongs to this contest
    problem = db.query(ContestProblem).filter(
        ContestProblem.id == payload.problem_id,
        ContestProblem.contest_id == contest_id
    ).first()
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found in this contest"
        )
    
    # Create submission
    submission = ContestSubmission(
        user_id=current_user.id,
        contest_id=contest_id,
        problem_id=payload.problem_id,
        language=payload.language,
        code=payload.code,
        verdict="PENDING",
        score=0
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@router.get("/{contest_id}/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(contest_id: int, db: Session = Depends(get_db)):
    """Get leaderboard/submissions for a contest"""
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Get all submissions with user and problem details
    submissions = db.query(
        ContestSubmission.user_id,
        User.name.label("user_name"),
        ContestSubmission.problem_id,
        ContestProblem.title.label("problem_title"),
        ContestSubmission.score,
        ContestSubmission.verdict,
        ContestSubmission.submitted_at
    ).join(
        User, ContestSubmission.user_id == User.id
    ).join(
        ContestProblem, ContestSubmission.problem_id == ContestProblem.id
    ).filter(
        ContestSubmission.contest_id == contest_id
    ).order_by(
        ContestSubmission.score.desc(),
        ContestSubmission.submitted_at.asc()
    ).all()
    
    return [
        LeaderboardEntry(
            user_id=s.user_id,
            user_name=s.user_name,
            problem_id=s.problem_id,
            problem_title=s.problem_title,
            score=s.score,
            verdict=s.verdict,
            submitted_at=s.submitted_at
        )
        for s in submissions
    ]


@router.get("/{contest_id}/my-submissions", response_model=List[SubmissionResponse])
def get_my_submissions(
    contest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's submissions for a contest"""
    submissions = db.query(ContestSubmission).filter(
        ContestSubmission.contest_id == contest_id,
        ContestSubmission.user_id == current_user.id
    ).order_by(ContestSubmission.submitted_at.desc()).all()
    
    return submissions
