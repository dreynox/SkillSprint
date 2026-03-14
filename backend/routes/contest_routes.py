from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import Contest, ContestProblem, ContestSubmission
from schemas import (
    ContestCreate,
    ContestOut,
    ContestProblemCreate,
    ContestProblemOut,
    ContestSubmissionCreate,
    ContestSubmissionOut,
    ContestWithProblems,
)

router = APIRouter()


@router.post("", response_model=ContestOut, status_code=status.HTTP_201_CREATED)
def create_contest(payload: ContestCreate, db: Session = Depends(get_db)):
    contest = Contest(**payload.model_dump())
    db.add(contest)
    db.commit()
    db.refresh(contest)
    return contest


@router.get("", response_model=List[ContestOut])
def list_contests(active_only: bool = Query(False), db: Session = Depends(get_db)):
    query = db.query(Contest)
    if active_only:
        query = query.filter(Contest.is_active.is_(True))
    return query.order_by(Contest.id.asc()).all()


@router.get("/{contest_id}", response_model=ContestWithProblems)
def get_contest(contest_id: int, db: Session = Depends(get_db)):
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")
    return contest


@router.post("/{contest_id}/problems", response_model=ContestProblemOut, status_code=status.HTTP_201_CREATED)
def add_problem(contest_id: int, payload: ContestProblemCreate, db: Session = Depends(get_db)):
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")

    problem = ContestProblem(contest_id=contest_id, **payload.model_dump())
    db.add(problem)
    db.commit()
    db.refresh(problem)
    return problem


@router.post(
    "/{contest_id}/problems/{problem_id}/submit",
    response_model=ContestSubmissionOut,
    status_code=status.HTTP_201_CREATED,
)
def submit_code(
    contest_id: int,
    problem_id: int,
    payload: ContestSubmissionCreate,
    db: Session = Depends(get_db),
):
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")

    problem = (
        db.query(ContestProblem)
        .filter(ContestProblem.id == problem_id, ContestProblem.contest_id == contest_id)
        .first()
    )
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found in this contest")

    submission = ContestSubmission(
        user_id=payload.user_id,
        contest_id=contest_id,
        problem_id=problem_id,
        language=payload.language,
        code=payload.code,
        verdict="PENDING",
        score=0,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@router.get("/{contest_id}/submissions", response_model=List[ContestSubmissionOut])
def list_contest_submissions(contest_id: int, db: Session = Depends(get_db)):
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")

    submissions = (
        db.query(ContestSubmission)
        .filter(ContestSubmission.contest_id == contest_id)
        .order_by(ContestSubmission.submitted_at.asc())
        .all()
    )
    return submissions
