from typing import List
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Contest, ContestParticipation, ContestProblem, ContestSubmission, TestCase, User
from schemas import (
    ContestCreate,
    ContestOut,
    ContestProblemCreate,
    ContestProblemOut,
    ContestParticipationOut,
    ContestSubmissionCreate,
    ContestSubmissionOut,
    ContestWithProblems,
    TestCaseCreate,
    TestCaseOut,
    CodeExecutionResponse,
)
from compiler import test_code

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
    current_user: User = Depends(get_current_user),
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
        user_id=current_user.id,
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


@router.post("/{contest_id}/join", response_model=ContestParticipationOut, status_code=status.HTTP_201_CREATED)
def join_contest(
    contest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")

    existing = (
        db.query(ContestParticipation)
        .filter(
            ContestParticipation.contest_id == contest_id,
            ContestParticipation.user_id == current_user.id,
        )
        .first()
    )
    if existing:
        return existing

    participation = ContestParticipation(user_id=current_user.id, contest_id=contest_id)
    db.add(participation)
    db.commit()
    db.refresh(participation)
    return participation


@router.post(
    "/{contest_id}/problems/{problem_id}/test-cases",
    response_model=TestCaseOut,
    status_code=status.HTTP_201_CREATED,
)
def add_test_case(
    contest_id: int,
    problem_id: int,
    payload: TestCaseCreate,
    db: Session = Depends(get_db),
):
    """Add a test case to a problem (admin only)"""
    problem = (
        db.query(ContestProblem)
        .filter(ContestProblem.id == problem_id, ContestProblem.contest_id == contest_id)
        .first()
    )
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    test_case = TestCase(
        problem_id=problem_id,
        input_data=payload.input_data,
        expected_output=payload.expected_output,
    )
    db.add(test_case)
    db.commit()
    db.refresh(test_case)
    return test_case


@router.get("/{contest_id}/problems/{problem_id}/test-cases", response_model=List[TestCaseOut])
def get_problem_test_cases(
    contest_id: int,
    problem_id: int,
    db: Session = Depends(get_db),
):
    """Get all test cases for a problem"""
    problem = (
        db.query(ContestProblem)
        .filter(ContestProblem.id == problem_id, ContestProblem.contest_id == contest_id)
        .first()
    )
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    test_cases = db.query(TestCase).filter(TestCase.problem_id == problem_id).all()
    return test_cases


@router.post(
    "/{contest_id}/problems/{problem_id}/execute",
    response_model=CodeExecutionResponse,
)
def execute_code_for_problem(
    contest_id: int,
    problem_id: int,
    payload: ContestSubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute code against test cases and return results"""
    problem = (
        db.query(ContestProblem)
        .filter(ContestProblem.id == problem_id, ContestProblem.contest_id == contest_id)
        .first()
    )
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    # Get test cases
    test_cases = db.query(TestCase).filter(TestCase.problem_id == problem_id).all()
    if not test_cases:
        return CodeExecutionResponse(
            status="NO_TESTS",
            message="No test cases available for this problem",
            passed=0,
            total=0,
        )

    # Convert to format expected by compiler
    test_data = [
        {"input": tc.input_data or "", "expected_output": tc.expected_output}
        for tc in test_cases
    ]

    # Only support C for now
    if payload.language.lower() not in ["c", "c99"]:
        return CodeExecutionResponse(
            status="UNSUPPORTED_LANGUAGE",
            message="Only C language is supported",
            passed=0,
            total=len(test_data),
        )

    # Execute code
    result = test_code(payload.code, test_data)

    # Convert TestResult objects from compiler
    test_results = []
    for res in result.get("results", []):
        test_results.append(
            {
                "test_case": res.get("test_case"),
                "status": res.get("status"),
                "input": res.get("input"),
                "expected": res.get("expected"),
                "actual": res.get("actual"),
                "error": res.get("error"),
            }
        )

    return CodeExecutionResponse(
        status=result.get("status"),
        message=result.get("message"),
        passed=result.get("passed", 0),
        total=result.get("total", 0),
        results=test_results,
    )
