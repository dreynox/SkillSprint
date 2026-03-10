from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import User, Quiz, QuizQuestion, QuizSubmission
from ..schemas import (
    QuizCreate,
    QuizResponse,
    QuestionCreate,
    QuestionResponse,
    QuestionAdminResponse,
    QuizSubmissionCreate,
    QuizSubmissionResponse,
    QuestionOut,
    Answer,
    SubmissionRequest,
    SubmissionResponse,
)
from ..auth import get_current_user, require_admin

router = APIRouter()


# ========== QUIZ ENDPOINTS ==========

@router.get("/", response_model=List[QuizResponse])
def list_quizzes(db: Session = Depends(get_db)):
    """Get all quizzes (public endpoint)"""
    quizzes = db.query(Quiz).all()
    return quizzes


@router.post("/", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def create_quiz(
    payload: QuizCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Create a new quiz (admin only)"""
    quiz = Quiz(**payload.model_dump())
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return quiz


@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    """Get quiz details"""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    return quiz


# ========== QUESTION ENDPOINTS ==========

@router.get("/{quiz_id}/questions", response_model=List[QuestionResponse])
def get_quiz_questions(quiz_id: int, db: Session = Depends(get_db)):
    """Get all questions in a quiz (without correct answers)"""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    if not quiz.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quiz is not active"
        )
    
    questions = db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == quiz_id
    ).all()
    return questions


@router.post(
    "/{quiz_id}/questions",
    response_model=QuestionAdminResponse,
    status_code=status.HTTP_201_CREATED
)
def add_question(
    quiz_id: int,
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Add a question to a quiz (admin only)"""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    question = QuizQuestion(
        quiz_id=quiz_id,
        **payload.model_dump()
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


# ========== SUBMISSION ENDPOINTS ==========

@router.post("/{quiz_id}/submit", response_model=QuizSubmissionResponse)
def submit_quiz(
    quiz_id: int,
    payload: QuizSubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit answers for a quiz"""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Load all questions for the quiz
    questions = db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == quiz_id
    ).all()
    
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quiz has no questions"
        )
    
    # Create a mapping of question_id -> question
    question_map = {q.id: q for q in questions}
    
    # Calculate score
    score = 0
    for answer in payload.answers:
        question = question_map.get(answer.question_id)
        if question and answer.selected.upper() == question.correct_option.upper():
            score += 1
    
    # Create submission
    submission = QuizSubmission(
        user_id=current_user.id,
        quiz_id=quiz_id,
        score=score,
        total_questions=len(questions)
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@router.get("/{quiz_id}/my-submissions", response_model=List[QuizSubmissionResponse])
def get_my_quiz_submissions(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's submissions for a quiz"""
    submissions = db.query(QuizSubmission).filter(
        QuizSubmission.quiz_id == quiz_id,
        QuizSubmission.user_id == current_user.id
    ).order_by(QuizSubmission.submitted_at.desc()).all()
    
    return submissions


# ========== ADMIN ENDPOINTS ==========

@router.get("/admin/{quiz_id}/questions", response_model=List[QuestionAdminResponse])
def get_quiz_questions_admin(
    quiz_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get all questions with correct answers (admin only)"""
    questions = db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == quiz_id
    ).all()
    return questions


@router.get("/admin/{quiz_id}/submissions", response_model=List[QuizSubmissionResponse])
def get_all_quiz_submissions(
    quiz_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get all submissions for a quiz (admin only)"""
    submissions = db.query(QuizSubmission).filter(
        QuizSubmission.quiz_id == quiz_id
    ).order_by(
        QuizSubmission.score.desc(),
        QuizSubmission.submitted_at.asc()
    ).all()
    
    return submissions


# ========== BACKWARD COMPATIBILITY ROUTES (from "backend for frontend") ==========
# These routes support the older "tests/" naming convention and simpler payloads

@router.get("/tests/{test_id}/questions", response_model=list)
def get_test_questions_legacy(test_id: int, db: Session = Depends(get_db)):
    """Legacy endpoint: Get test questions (uses 'test' instead of 'quiz')"""
    quiz = db.query(Quiz).filter(Quiz.id == test_id).first()
    if not quiz or not quiz.is_active:
        raise HTTPException(status_code=404, detail="Test not found or inactive")
    
    questions = db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == test_id
    ).all()
    
    # Return in simplified format
    return [
        {
            "id": q.id,
            "text": q.text,
            "option_a": q.option_a,
            "option_b": q.option_b,
            "option_c": q.option_c,
            "option_d": q.option_d,
        }
        for q in questions
    ]


@router.post("/tests/{test_id}/submit", response_model=SubmissionResponse)
def submit_test_legacy(
    test_id: int,
    payload: SubmissionRequest,
    db: Session = Depends(get_db),
):
    """Legacy endpoint: Submit test answers (uses 'test' instead of 'quiz', accepts user_id in payload)"""
    quiz = db.query(Quiz).filter(Quiz.id == test_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Load all questions for that quiz
    questions = db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == test_id
    ).all()
    qmap = {q.id: q for q in questions}
    
    score = 0
    for ans in payload.answers:
        q = qmap.get(ans.question_id)
        if not q:
            continue
        if ans.selected.upper() == q.correct_option.upper():
            score += 1
    
    # Create submission with the provided user_id
    submission = QuizSubmission(
        user_id=payload.user_id,
        quiz_id=test_id,
        score=score,
        total_questions=len(questions)
    )
    db.add(submission)
    db.commit()
    
    return SubmissionResponse(score=score, total=len(questions))


@router.get("/admin/tests/{test_id}/submissions")
def get_test_submissions_legacy(test_id: int, db: Session = Depends(get_db)):
    """Legacy endpoint: Get test submissions (admin endpoint, accepts 'test' instead of 'quiz')"""
    subs = db.query(QuizSubmission).filter(
        QuizSubmission.quiz_id == test_id
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
