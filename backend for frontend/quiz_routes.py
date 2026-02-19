from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas

router = APIRouter()


@router.get("/tests/{test_id}/questions", response_model=list[schemas.QuestionOut])
def get_test_questions(test_id: int, db: Session = Depends(get_db)):
    test = db.query(models.Test).filter(models.Test.id == test_id).first()
    if not test or not test.is_active:
        raise HTTPException(status_code=404, detail="Test not found or inactive")

    questions = db.query(models.Question).filter(
        models.Question.test_id == test_id
    ).all()

    return questions


@router.post("/tests/{test_id}/submit", response_model=schemas.SubmissionResponse)
def submit_test(
    test_id: int,
    payload: schemas.SubmissionRequest,
    db: Session = Depends(get_db),
):
    test = db.query(models.Test).filter(models.Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Load all questions for that test into a dict
    questions = db.query(models.Question).filter(
        models.Question.test_id == test_id
    ).all()
    qmap = {q.id: q for q in questions}

    score = 0
    for ans in payload.answers:
        q = qmap.get(ans.question_id)
        if not q:
            continue
        if ans.selected.upper() == q.correct_option.upper():
            score += 1

    submission = models.Submission(
        user_id=payload.user_id,
        test_id=test_id,
        score=score,
    )
    db.add(submission)
    db.commit()

    return schemas.SubmissionResponse(score=score, total=len(questions))


@router.get("/admin/tests/{test_id}/submissions")
def get_test_submissions(test_id: int, db: Session = Depends(get_db)):
    subs = db.query(models.Submission).filter(
        models.Submission.test_id == test_id
    ).all()
    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "score": s.score,
            "submitted_at": s.submitted_at,
        }
        for s in subs
    ]
