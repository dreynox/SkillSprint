from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "student"
    srn: Optional[str] = None
    prn: Optional[str] = None
    year: Optional[int] = None
    branch: Optional[str] = None
    division: Optional[str] = None
    roll_no: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters")
        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordVerifyRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, value: str) -> str:
        code = value.strip()
        if len(code) != 6 or not code.isdigit():
            raise ValueError("OTP must be a 6-digit number")
        return code

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters")
        return value


class MessageResponse(BaseModel):
    message: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    srn: Optional[str]
    prn: Optional[str]
    year: Optional[int]
    branch: Optional[str]
    division: Optional[str]
    roll_no: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    message: str
    user: UserOut
    token: Optional[str] = None


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    srn: Optional[str] = None
    prn: Optional[str] = None
    year: Optional[int] = None
    branch: Optional[str] = None
    division: Optional[str] = None
    roll_no: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class UserStatsOut(BaseModel):
    contests_joined: int
    contest_submissions: int
    quiz_attempts: int
    total_quiz_score: int
    quiz_questions_attempted: int


class ContestParticipationOut(BaseModel):
    id: int
    user_id: int
    contest_id: int
    joined_at: datetime

    class Config:
        from_attributes = True


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


class RandomQuizStartRequest(BaseModel):
    language: str
    level: str
    question_count: int = Field(default=20, ge=1, le=100)


class RandomQuizQuestionOut(BaseModel):
    question_id: int
    question: str
    options: dict[str, str]


class RandomQuizStartResponse(BaseModel):
    session_id: str
    language: str
    level: str
    question_count: int
    total_pool: int
    questions: List[RandomQuizQuestionOut]


class RandomQuizSubmitRequest(BaseModel):
    user_id: Optional[int] = None
    answers: List[Answer]


class RandomQuizSubmitResponse(BaseModel):
    score: int
    total: int
    unanswered: int


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


class TestCaseCreate(BaseModel):
    input_data: Optional[str] = None
    expected_output: str


class TestCaseOut(BaseModel):
    id: int
    problem_id: int
    input_data: Optional[str]
    expected_output: str
    created_at: datetime

    class Config:
        from_attributes = True


class TestResult(BaseModel):
    test_case: int
    status: str  # PASS, FAIL, RUNTIME_ERROR, TIMEOUT
    input: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None
    error: Optional[str] = None


class CodeExecutionResponse(BaseModel):
    status: str  # ACCEPTED, PARTIAL, COMPILATION_ERROR, RUNTIME_ERROR
    message: Optional[str] = None
    passed: int
    total: int
    results: List[TestResult] = []


class ContestWithProblems(ContestOut):
    problems: List[ContestProblemOut]


class ContestSubmissionCreate(BaseModel):
    user_id: Optional[int] = None
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
    execution_results: Optional[str] = None
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


class MessageCreate(BaseModel):
    recipient_id: int
    content: Optional[str] = None
    media_type: Optional[str] = None


class MessageOut(BaseModel):
    id: int
    sender_id: int
    recipient_id: int
    content: Optional[str]
    media_type: Optional[str]
    file_path: Optional[str]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MessageWithSender(MessageOut):
    sender: UserOut


class FollowOut(BaseModel):
    id: int
    follower_id: int
    following_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SearchResult(BaseModel):
    type: str  # "user", "contest", "hackathon"
    id: int
    name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    bio: Optional[str] = None
