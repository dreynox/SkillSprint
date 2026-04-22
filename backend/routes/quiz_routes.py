import json
import random
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from auth import get_current_user, require_admin
from database import get_db
from models import Question, QuizSubmission, Test, User
from schemas import (
    QuizAdminSubmissionOut,
    QuizQuestionCreate,
    QuizTestCreate,
    QuestionOut,
    QuizSubmissionRequest,
    QuizSubmissionResponse,
    RandomQuizStartRequest,
    RandomQuizStartResponse,
    RandomQuizSubmitRequest,
    RandomQuizSubmitResponse,
    TestOut,
)

router = APIRouter()

RANDOM_QUIZ_SESSIONS = {}
SESSION_TTL_SECONDS = 6 * 60 * 60


def _cleanup_expired_sessions() -> None:
    now = time.time()
    expired = [
        key
        for key, value in RANDOM_QUIZ_SESSIONS.items()
        if now - value.get("created_at", now) > SESSION_TTL_SECONDS
    ]
    for key in expired:
        RANDOM_QUIZ_SESSIONS.pop(key, None)


def _resolve_folder_case_insensitive(parent: Path, desired_name: str) -> Path | None:
    desired = desired_name.strip().lower()
    for child in parent.iterdir():
        if child.is_dir() and child.name.lower() == desired:
            return child
    return None


def _load_language_level_questions(language: str, level: str) -> list[dict]:
    base = Path(__file__).resolve().parents[2] / "Database" / "Q&A Topics" / "Computer Languages"
    if not base.exists():
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Question bank base folder not found")

    lang_dir = _resolve_folder_case_insensitive(base, language)
    if not lang_dir:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language folder not found")

    level_dir = _resolve_folder_case_insensitive(lang_dir, level)
    if not level_dir:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Level folder not found")

    files = sorted(level_dir.glob("Set-*.json"))
    if not files:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No set files found for the selected language and level")

    questions: list[dict] = []
    for file_path in files:
        with file_path.open("r", encoding="utf-8-sig") as source:
            payload = json.load(source)
            for item in payload.get("questions", []):
                options = item.get("options", {})
                answer = str(item.get("answer", "")).strip().upper()
                if answer not in {"A", "B", "C", "D"}:
                    continue
                if not all(key in options for key in ["A", "B", "C", "D"]):
                    continue

                questions.append(
                    {
                        "question": item.get("question", ""),
                        "options": {
                            "A": options.get("A", ""),
                            "B": options.get("B", ""),
                            "C": options.get("C", ""),
                            "D": options.get("D", ""),
                        },
                        "answer": answer,
                    }
                )

    if not questions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid questions found in the selected bank")

    return questions


@router.get("/tests", response_model=List[TestOut])
def list_tests(active_only: bool = Query(False), db: Session = Depends(get_db)):
    query = db.query(Test)
    if active_only:
        query = query.filter(Test.is_active.is_(True))
    return query.order_by(Test.id.asc()).all()


@router.get("/admin/tests", response_model=List[TestOut])
def list_tests_for_admin(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return db.query(Test).order_by(Test.id.asc()).all()


@router.post("/admin/tests", response_model=TestOut, status_code=status.HTTP_201_CREATED)
def create_test(
    payload: QuizTestCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    test = Test(**payload.model_dump())
    db.add(test)
    db.commit()
    db.refresh(test)
    return test


@router.post("/admin/tests/{test_id}/questions", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
def add_test_question(
    test_id: int,
    payload: QuizQuestionCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    question = Question(test_id=test_id, **payload.model_dump())
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.get("/tests/{test_id}/questions", response_model=List[QuestionOut])
def get_test_questions(test_id: int, db: Session = Depends(get_db)):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if test.start_time and now < test.start_time:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Test has not started yet")
    if test.end_time and now > test.end_time:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Test has ended")

    questions = db.query(Question).filter(Question.test_id == test_id).order_by(Question.id.asc()).all()
    return questions


@router.post("/tests/{test_id}/submit", response_model=QuizSubmissionResponse)
def submit_test_answers(
    test_id: int,
    payload: QuizSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if test.start_time and now < test.start_time:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Test has not started yet")
    if test.end_time and now > test.end_time:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Test has ended")

    questions = db.query(Question).filter(Question.test_id == test_id).all()
    if not questions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This test has no questions")

    question_map = {question.id: question for question in questions}
    score = 0

    for answer in payload.answers:
        question = question_map.get(answer.question_id)
        if question and answer.selected.upper() == question.correct_option.upper():
            score += 1

    submission = QuizSubmission(
        user_id=current_user.id,
        test_id=test_id,
        score=score,
        total_questions=len(questions),
    )
    db.add(submission)
    db.commit()

    return QuizSubmissionResponse(score=score, total=len(questions))


@router.get("/admin/tests/{test_id}/submissions")
def get_test_submissions(
    test_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    submissions = (
        db.query(QuizSubmission, User)
        .join(User, QuizSubmission.user_id == User.id)
        .filter(QuizSubmission.test_id == test_id)
        .order_by(QuizSubmission.score.desc(), QuizSubmission.submitted_at.asc())
        .all()
    )

    return [
        QuizAdminSubmissionOut(
            user_id=submission.user_id,
            user_name=user.name,
            user_email=user.email,
            score=submission.score,
            total_questions=submission.total_questions,
            submitted_at=submission.submitted_at,
        )
        for submission, user in submissions
    ]


@router.post("/random-bank/start", response_model=RandomQuizStartResponse)
def start_random_bank_session(payload: RandomQuizStartRequest):
    _cleanup_expired_sessions()

    pool = _load_language_level_questions(payload.language, payload.level)
    if payload.question_count > len(pool):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Requested {payload.question_count} questions, but only {len(pool)} available",
        )

    selected = random.sample(pool, payload.question_count)

    session_id = str(uuid.uuid4())
    questions_for_client = []
    answers = {}

    for index, question in enumerate(selected, start=1):
        answers[index] = question["answer"]
        questions_for_client.append(
            {
                "question_id": index,
                "question": question["question"],
                "options": question["options"],
            }
        )

    RANDOM_QUIZ_SESSIONS[session_id] = {
        "created_at": time.time(),
        "language": payload.language,
        "level": payload.level,
        "answers": answers,
        "total": payload.question_count,
    }

    return RandomQuizStartResponse(
        session_id=session_id,
        language=payload.language,
        level=payload.level,
        question_count=payload.question_count,
        total_pool=len(pool),
        questions=questions_for_client,
    )


@router.post("/random-bank/{session_id}/submit", response_model=RandomQuizSubmitResponse)
def submit_random_bank_session(session_id: str, payload: RandomQuizSubmitRequest):
    _cleanup_expired_sessions()

    session = RANDOM_QUIZ_SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or expired")

    answers_map = session["answers"]
    total = session["total"]
    answered = 0
    score = 0

    for answer in payload.answers:
        correct = answers_map.get(answer.question_id)
        if not correct:
            continue
        answered += 1
        if answer.selected.upper() == correct:
            score += 1

    return RandomQuizSubmitResponse(score=score, total=total, unanswered=max(total - answered, 0))
