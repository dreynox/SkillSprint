from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime

# ========== AUTH SCHEMAS ==========

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    year: Optional[int] = None
    branch: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_length(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    year: Optional[int]
    branch: Optional[str]
    role: str

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ========== CONTEST SCHEMAS ==========

class ContestCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_active: bool = False

class ContestResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProblemCreate(BaseModel):
    title: str
    statement: str
    difficulty: Optional[str] = "Medium"
    max_score: int = 100

class ProblemResponse(BaseModel):
    id: int
    contest_id: int
    title: str
    statement: str
    difficulty: Optional[str]
    max_score: int

    class Config:
        from_attributes = True


class SubmissionCreate(BaseModel):
    problem_id: int
    language: Optional[str] = "Python"
    code: str

class SubmissionResponse(BaseModel):
    id: int
    user_id: int
    contest_id: int
    problem_id: int
    language: Optional[str]
    verdict: str
    score: int
    submitted_at: datetime

    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    user_id: int
    user_name: str
    problem_id: int
    problem_title: str
    score: int
    verdict: str
    submitted_at: datetime

    class Config:
        from_attributes = True


# ========== QUIZ (MCQ) SCHEMAS ==========

class QuizCreate(BaseModel):
    title: str
    description: Optional[str] = None
    is_active: bool = False
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class QuizResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    is_active: bool
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str  # "A" / "B" / "C" / "D"

    @field_validator("correct_option")
    @classmethod
    def validate_option(cls, v):
        if v.upper() not in ["A", "B", "C", "D"]:
            raise ValueError("correct_option must be A, B, C, or D")
        return v.upper()


class QuestionResponse(BaseModel):
    """Public question response (without correct answer)"""
    id: int
    quiz_id: int
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str

    class Config:
        from_attributes = True


class QuestionAdminResponse(BaseModel):
    """Admin question response (with correct answer)"""
    id: int
    quiz_id: int
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str

    class Config:
        from_attributes = True


class QuizAnswer(BaseModel):
    question_id: int
    selected: str  # "A" / "B" / "C" / "D"


class QuizSubmissionCreate(BaseModel):
    answers: List[QuizAnswer]


class QuizSubmissionResponse(BaseModel):
    id: int
    user_id: int
    quiz_id: int
    score: int
    total_questions: int
    submitted_at: datetime

    class Config:
        from_attributes = True


# ========== BACKWARD COMPATIBILITY SCHEMAS (from "backend for frontend") ==========

class QuestionOut(BaseModel):
    """Simplified question output (same as QuestionResponse)"""
    id: int
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str

    class Config:
        from_attributes = True


class Answer(BaseModel):
    """Simplified answer format (same as QuizAnswer)"""
    question_id: int
    selected: str  # "A" / "B" / "C" / "D"


class SubmissionRequest(BaseModel):
    """Simplified submission request (same as QuizSubmissionCreate)"""
    user_id: int          # For backward compatibility; use auth for new code
    answers: List[Answer]


class SubmissionResponse(BaseModel):
    """Simplified submission response"""
    score: int
    total: int
