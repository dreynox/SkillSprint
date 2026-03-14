from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import Question, QuizSubmission, Test
from schemas import QuestionOut, QuizSubmissionRequest, QuizSubmissionResponse, TestOut

router = APIRouter()


@router.get("/tests", response_model=List[TestOut])
def list_tests(active_only: bool = Query(False), db: Session = Depends(get_db)):
    query = db.query(Test)
    if active_only:
        query = query.filter(Test.is_active.is_(True))
    return query.order_by(Test.id.asc()).all()


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
def submit_test_answers(test_id: int, payload: QuizSubmissionRequest, db: Session = Depends(get_db)):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

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
        user_id=payload.user_id,
        test_id=test_id,
        score=score,
        total_questions=len(questions),
    )
    db.add(submission)
    db.commit()

    return QuizSubmissionResponse(score=score, total=len(questions))


@router.get("/admin/tests/{test_id}/submissions")
def get_test_submissions(test_id: int, db: Session = Depends(get_db)):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    submissions = (
        db.query(QuizSubmission)
        .filter(QuizSubmission.test_id == test_id)
        .order_by(QuizSubmission.score.desc(), QuizSubmission.submitted_at.asc())
        .all()
    )

    return [
        {
            "user_id": submission.user_id,
            "score": submission.score,
            "submitted_at": submission.submitted_at,
        }
        for submission in submissions
    ]
