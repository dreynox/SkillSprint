from datetime import datetime
import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class RoleEnum(str, enum.Enum):
    STUDENT = "student"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.STUDENT, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    questions = relationship("Question", back_populates="test", cascade="all, delete-orphan")
    submissions = relationship("QuizSubmission", back_populates="test", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    text = Column(Text, nullable=False)
    option_a = Column(String, nullable=False)
    option_b = Column(String, nullable=False)
    option_c = Column(String, nullable=False)
    option_d = Column(String, nullable=False)
    correct_option = Column(String(1), nullable=False)

    test = relationship("Test", back_populates="questions")


class QuizSubmission(Base):
    __tablename__ = "quiz_submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    test_id = Column("quiz_id", Integer, ForeignKey("tests.id"), nullable=False)
    score = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")
    test = relationship("Test", back_populates="submissions")


class Contest(Base):
    __tablename__ = "contests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    problems = relationship("ContestProblem", back_populates="contest", cascade="all, delete-orphan")
    submissions = relationship("ContestSubmission", back_populates="contest", cascade="all, delete-orphan")


class ContestProblem(Base):
    __tablename__ = "contest_problems"

    id = Column(Integer, primary_key=True, index=True)
    contest_id = Column(Integer, ForeignKey("contests.id"), nullable=False)
    title = Column(String, nullable=False)
    statement = Column(Text, nullable=False)
    difficulty = Column(String, nullable=True)
    tags = Column(String, nullable=True)

    contest = relationship("Contest", back_populates="problems")
    submissions = relationship("ContestSubmission", back_populates="problem", cascade="all, delete-orphan")


class ContestSubmission(Base):
    __tablename__ = "contest_submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contest_id = Column(Integer, ForeignKey("contests.id"), nullable=False)
    problem_id = Column(Integer, ForeignKey("contest_problems.id"), nullable=False)
    language = Column(String, nullable=False)
    code = Column(Text, nullable=False)
    verdict = Column(String, default="PENDING", nullable=False)
    score = Column(Integer, default=0, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")
    contest = relationship("Contest", back_populates="submissions")
    problem = relationship("ContestProblem", back_populates="submissions")
