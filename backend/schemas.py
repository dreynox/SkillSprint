from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "student"

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters")
        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    message: str
    user: UserOut
    token: Optional[str] = None


class TestOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    is_active: bool
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionOut(BaseModel):
    id: int
    test_id: int
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str

    class Config:
        from_attributes = True


class Answer(BaseModel):
    question_id: int
    selected: str

    @field_validator("selected")
    @classmethod
    def validate_selected(cls, value: str) -> str:
        option = value.upper()
        if option not in {"A", "B", "C", "D"}:
            raise ValueError("selected must be one of A, B, C, D")
        return option


class QuizSubmissionRequest(BaseModel):
    user_id: int
    answers: List[Answer]


class QuizSubmissionResponse(BaseModel):
    score: int
    total: int


class QuizSubmissionOut(BaseModel):
    id: int
    user_id: int
    test_id: int
    score: int
    total_questions: int
    submitted_at: datetime

    class Config:
        from_attributes = True


class ContestCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_active: bool = False


class ContestProblemCreate(BaseModel):
    title: str
    statement: str
    difficulty: Optional[str] = None
    tags: Optional[str] = None


class ContestProblemOut(BaseModel):
    id: int
    contest_id: int
    title: str
    statement: str
    difficulty: Optional[str]
    tags: Optional[str]

    class Config:
        from_attributes = True


class ContestOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ContestWithProblems(ContestOut):
    problems: List[ContestProblemOut]


class ContestSubmissionCreate(BaseModel):
    user_id: int
    language: str
    code: str


class ContestSubmissionOut(BaseModel):
    id: int
    user_id: int
    contest_id: int
    problem_id: int
    language: str
    code: str
    verdict: str
    score: int
    submitted_at: datetime

    class Config:
        from_attributes = True


class HackathonCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_active: bool = False


class HackathonOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
