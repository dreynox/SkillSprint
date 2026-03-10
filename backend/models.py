from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base

class RoleEnum(str, enum.Enum):
    STUDENT = "student"
    ADMIN = "admin"
    FACULTY = "faculty"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    year = Column(Integer)  # 1, 2, 3, 4
    branch = Column(String)  # CSE, ECE, Mechanical, etc.
    role = Column(Enum(RoleEnum), default=RoleEnum.STUDENT)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ========== CONTEST MODELS ==========

class Contest(Base):
    __tablename__ = "contests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    problems = relationship("ContestProblem", back_populates="contest", cascade="all, delete-orphan")
    submissions = relationship("ContestSubmission", back_populates="contest", cascade="all, delete-orphan")


class ContestProblem(Base):
    __tablename__ = "contest_problems"

    id = Column(Integer, primary_key=True, index=True)
    contest_id = Column(Integer, ForeignKey("contests.id"), nullable=False)
    title = Column(String, nullable=False)
    statement = Column(String, nullable=False)  # Problem description or URL
    difficulty = Column(String, nullable=True)  # Easy/Medium/Hard
    max_score = Column(Integer, default=100)

    contest = relationship("Contest", back_populates="problems")
    submissions = relationship("ContestSubmission", back_populates="problem", cascade="all, delete-orphan")


class ContestSubmission(Base):
    __tablename__ = "contest_submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contest_id = Column(Integer, ForeignKey("contests.id"), nullable=False)
    problem_id = Column(Integer, ForeignKey("contest_problems.id"), nullable=False)
    language = Column(String, nullable=True)  # Python/C++/Java/etc
    code = Column(String, nullable=False)  # Raw code submission
    verdict = Column(String, default="PENDING")  # PENDING/ACCEPTED/REJECTED/ERROR
    score = Column(Integer, default=0)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    contest = relationship("Contest", back_populates="submissions")
    problem = relationship("ContestProblem", back_populates="submissions")
    user = relationship("User")


# ========== QUIZ (MCQ) MODELS ==========

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    submissions = relationship("QuizSubmission", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    text = Column(String, nullable=False)
    option_a = Column(String, nullable=False)
    option_b = Column(String, nullable=False)
    option_c = Column(String, nullable=False)
    option_d = Column(String, nullable=False)
    correct_option = Column(String, nullable=False)  # "A" / "B" / "C" / "D"

    quiz = relationship("Quiz", back_populates="questions")


class QuizSubmission(Base):
    __tablename__ = "quiz_submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    score = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    quiz = relationship("Quiz", back_populates="submissions")
    user = relationship("User")
