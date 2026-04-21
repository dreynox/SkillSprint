from typing import List
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from auth import get_current_user, require_admin
from database import get_db
from models import Contest, ContestParticipation, ContestProblem, ContestSubmission, TestCase, User
from schemas import (
    ContestSubmissionAdminOut,
    ContestCreate,
    ContestOut,
    ContestProblemCreate,
    ContestProblemOut,
    ContestParticipationOut,
    ContestSubmissionCreate,
    ContestSubmissionDirectCreate,
    ContestSubmissionOut,
    ContestWithProblems,
    TestCaseCreate,
    TestCaseOut,
    CodeExecutionResponse,
)
from compiler import test_code

router = APIRouter()


def _evaluate_submission(db: Session, problem_id: int, language: str, code: str) -> tuple[str, int, str]:
    test_cases = db.query(TestCase).filter(TestCase.problem_id == problem_id).all()

    if not test_cases:
        payload = {
            "status": "NO_TESTS",
            "message": "No test cases available for this problem",
            "passed": 0,
            "total": 0,
            "results": [],
        }
        return "NO_TESTS", 0, json.dumps(payload)

    test_data = [{"input": tc.input_data or "", "expected_output": tc.expected_output} for tc in test_cases]
    result = test_code(code, test_data, language)

    status = str(result.get("status") or "PENDING").upper()
    passed = int(result.get("passed") or 0)
    total = int(result.get("total") or 0)
    score = int(round((passed / total) * 100)) if total > 0 else 0

    verdict_map = {
        "ACCEPTED": "ACCEPTED",
        "PARTIAL": "PARTIAL",
        "COMPILATION_ERROR": "COMPILATION_ERROR",
        "TOOL_UNAVAILABLE": "TOOL_UNAVAILABLE",
        "UNSUPPORTED_LANGUAGE": "UNSUPPORTED_LANGUAGE",
        "WEB_PREVIEW_ONLY": "WEB_PREVIEW_ONLY",
        "NO_TESTS": "NO_TESTS",
    }
    verdict = verdict_map.get(status, "PENDING")

    try:
        execution_results = json.dumps(result)
    except Exception:
        execution_results = json.dumps({"status": "ERROR", "message": "Failed to serialize execution result"})

    return verdict, score, execution_results


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


@router.get("/admin/submissions", response_model=List[ContestSubmissionAdminOut])
def list_all_submissions_for_admin(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    submissions = (
        db.query(ContestSubmission, User, Contest, ContestProblem)
        .join(User, ContestSubmission.user_id == User.id)
        .join(Contest, ContestSubmission.contest_id == Contest.id)
        .join(ContestProblem, ContestSubmission.problem_id == ContestProblem.id)
        .order_by(ContestSubmission.submitted_at.desc())
        .all()
    )

    result: List[ContestSubmissionAdminOut] = []
    for submission, user, contest, problem in submissions:
        parsed_execution = None
        if submission.execution_results:
            try:
                parsed_execution = json.loads(submission.execution_results)
            except Exception:
                parsed_execution = {"raw": submission.execution_results}

        result.append(
            ContestSubmissionAdminOut(
                id=submission.id,
                contest_id=contest.id,
                contest_name=contest.name,
                problem_id=problem.id,
                problem_title=problem.title,
                user_id=user.id,
                user_name=user.name,
                user_email=user.email,
                srn=user.srn,
                prn=user.prn,
                year=user.year,
                branch=user.branch,
                division=user.division,
                roll_no=user.roll_no,
                language=submission.language,
                verdict=submission.verdict,
                score=submission.score,
                submitted_at=submission.submitted_at,
                execution_results=parsed_execution,
            )
        )

    return result


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


@router.get("/{contest_id}/problems/{problem_id}", response_model=ContestProblemOut)
def get_problem(contest_id: int, problem_id: int, db: Session = Depends(get_db)):
    problem = (
        db.query(ContestProblem)
        .filter(ContestProblem.id == problem_id, ContestProblem.contest_id == contest_id)
        .first()
    )
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found in this contest")
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

    verdict, score, execution_results = _evaluate_submission(
        db=db,
        problem_id=problem_id,
        language=payload.language,
        code=payload.code,
    )

    submission = ContestSubmission(
        user_id=current_user.id,
        contest_id=contest_id,
        problem_id=problem_id,
        language=payload.language,
        code=payload.code,
        verdict=verdict,
        score=score,
        execution_results=execution_results,
    )
    try:
        db.add(submission)
        db.commit()
        db.refresh(submission)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist contest submission: {exc.__class__.__name__}",
        ) from exc
    return submission


@router.post(
    "/{contest_id}/submissions",
    response_model=ContestSubmissionOut,
    status_code=status.HTTP_201_CREATED,
)
def submit_code_legacy_path(
    contest_id: int,
    payload: ContestSubmissionDirectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Backward-compatible submission path used by older frontend builds."""
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")

    problem = (
        db.query(ContestProblem)
        .filter(ContestProblem.id == payload.problem_id, ContestProblem.contest_id == contest_id)
        .first()
    )
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found in this contest")

    verdict, score, execution_results = _evaluate_submission(
        db=db,
        problem_id=payload.problem_id,
        language=payload.language,
        code=payload.code,
    )

    submission = ContestSubmission(
        user_id=current_user.id,
        contest_id=contest_id,
        problem_id=payload.problem_id,
        language=payload.language,
        code=payload.code,
        verdict=verdict,
        score=score,
        execution_results=execution_results,
    )
    try:
        db.add(submission)
        db.commit()
        db.refresh(submission)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist contest submission: {exc.__class__.__name__}",
        ) from exc
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

    # Execute code for selected language
    result = test_code(payload.code, test_data, payload.language)

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
