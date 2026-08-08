from datetime import datetime
import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
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
    srn = Column(String, nullable=True)
    prn = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    branch = Column(String, nullable=True)
    division = Column(String, nullable=True)
    roll_no = Column(String, nullable=True)
    domain = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String, nullable=True)
    is_premium = Column(Boolean, default=False, nullable=False)
    premium_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    extra_xp = Column(Integer, default=0, nullable=False)


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
    explanation = Column(Text, nullable=True)

    test = relationship("Test", back_populates="questions")


class QuizSubmission(Base):
    __tablename__ = "quiz_submissions"
    __table_args__ = (
        Index(
            "ix_quiz_submissions_user_submitted_at",
            "user_id",
            "submitted_at",
        ),
        Index(
            "ix_quiz_submissions_test_submitted_at",
            "quiz_id",
            "submitted_at",
        ),
    )

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
    test_cases = relationship("TestCase", back_populates="problem", cascade="all, delete-orphan")
    submissions = relationship("ContestSubmission", back_populates="problem", cascade="all, delete-orphan")


class ContestSubmission(Base):
    __tablename__ = "contest_submissions"
    __table_args__ = (
        Index(
            "ix_contest_submissions_user_submitted_at",
            "user_id",
            "submitted_at",
        ),
        Index(
            "ix_contest_submissions_contest_submitted_at",
            "contest_id",
            "submitted_at",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contest_id = Column(Integer, ForeignKey("contests.id"), nullable=False)
    problem_id = Column(Integer, ForeignKey("contest_problems.id"), nullable=False)
    language = Column(String, nullable=False)
    code = Column(Text, nullable=False)
    verdict = Column(String, default="PENDING", nullable=False)
    score = Column(Integer, default=0, nullable=False)
    execution_results = Column(Text, nullable=True)  # JSON string of test results
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")
    contest = relationship("Contest", back_populates="submissions")
    problem = relationship("ContestProblem", back_populates="submissions")


class ContestParticipation(Base):
    __tablename__ = "contest_participations"
    __table_args__ = (UniqueConstraint("user_id", "contest_id", name="uq_user_contest"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contest_id = Column(Integer, ForeignKey("contests.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")
    contest = relationship("Contest")


class Hackathon(Base):
    __tablename__ = "hackathons"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("contest_problems.id"), nullable=False)
    input_data = Column(Text, nullable=True)  # Expected input
    expected_output = Column(Text, nullable=False)  # Expected output
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    problem = relationship("ContestProblem", back_populates="test_cases")


class PasswordResetOTP(Base):
    __tablename__ = "password_reset_otps"
    __table_args__ = (
        Index(
            "ix_password_reset_otps_email_consumed_created_at",
            "email",
            "consumed",
            "created_at",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    otp_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    consumed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index(
            "ix_messages_sender_recipient_created_at",
            "sender_id",
            "recipient_id",
            "created_at",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=True)
    media_type = Column(String, nullable=True)  # "text", "image", "video", "file", "voice"
    file_path = Column(String, nullable=True)  # Path to uploaded file/media
    expires_at = Column(DateTime, nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    sender = relationship("User", foreign_keys=[sender_id])
    recipient = relationship("User", foreign_keys=[recipient_id])


class Follow(Base):
    __tablename__ = "follows"
    __table_args__ = (UniqueConstraint("follower_id", "following_id", name="uq_follower_following"),)

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    following_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    follower = relationship("User", foreign_keys=[follower_id])
    following_user = relationship("User", foreign_keys=[following_id])
