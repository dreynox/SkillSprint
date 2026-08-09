from datetime import UTC, datetime, timedelta

from database import Base, SessionLocal, engine, ensure_database_indexes, ensure_sqlite_compatibility
from models import Contest, ContestProblem, Question, RoleEnum, Test, User
from auth import hash_password


def seed_users(db):
    if not db.query(User).filter(User.email == "admin@skillsprint-demo.com").first():
        db.add(
            User(
                name="Admin User",
                email="admin@skillsprint-demo.com",
                password_hash=hash_password("admin123"),
                role=RoleEnum.ADMIN,
            )
        )

    if not db.query(User).filter(User.email == "student@skillsprint.com").first():
        db.add(
            User(
                name="Test Student",
                email="student@skillsprint.com",
                password_hash=hash_password("student123"),
                role=RoleEnum.STUDENT,
            )
        )

    db.commit()


def seed_quiz(db):
    test = db.query(Test).filter(Test.title == "Python Basics Test").first()
    if not test:
        now = datetime.now(UTC).replace(tzinfo=None)
        test = Test(
            title="Python Basics Test",
            description="Simple MCQ round for skill assessment",
            is_active=True,
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(days=2),
        )
        db.add(test)
        db.commit()
        db.refresh(test)

    question_specs = [
        {
            "text": "Which keyword defines a function in Python?",
            "option_a": "func",
            "option_b": "def",
            "option_c": "function",
            "option_d": "lambda",
            "correct_option": "B",
        },
        {
            "text": "What is the output type of len('SkillSprint')?",
            "option_a": "str",
            "option_b": "float",
            "option_c": "int",
            "option_d": "list",
            "correct_option": "C",
        },
        {
            "text": "Which data structure uses key-value pairs?",
            "option_a": "list",
            "option_b": "tuple",
            "option_c": "set",
            "option_d": "dict",
            "correct_option": "D",
        },
    ]

    for spec in question_specs:
        exists = db.query(Question).filter(Question.test_id == test.id, Question.text == spec["text"]).first()
        if not exists:
            db.add(Question(test_id=test.id, **spec))

    db.commit()


def seed_contest(db):
    contest = db.query(Contest).filter(Contest.name == "Weekly Coding Sprint").first()
    if not contest:
        now = datetime.now(UTC).replace(tzinfo=None)
        contest = Contest(
            name="Weekly Coding Sprint",
            description="Competitive coding contest with multiple difficulty levels",
            start_time=now - timedelta(hours=2),
            end_time=now + timedelta(days=1),
            is_active=True,
        )
        db.add(contest)
        db.commit()
        db.refresh(contest)

    problem_specs = [
        {
            "title": "Sum of Two Numbers",
            "statement": "Read two integers and print their sum.",
            "difficulty": "Easy",
            "tags": "math,basics",
        },
        {
            "title": "Reverse a String",
            "statement": "Given a string, output the reverse string.",
            "difficulty": "Easy",
            "tags": "strings",
        },
    ]

    for spec in problem_specs:
        exists = db.query(ContestProblem).filter(
            ContestProblem.contest_id == contest.id,
            ContestProblem.title == spec["title"],
        ).first()
        if not exists:
            db.add(ContestProblem(contest_id=contest.id, **spec))

    db.commit()


if __name__ == "__main__":
    ensure_sqlite_compatibility()
    Base.metadata.create_all(bind=engine)
    ensure_database_indexes()
    db = SessionLocal()
    try:
        seed_users(db)
        seed_quiz(db)
        seed_contest(db)
        print("Seed data inserted (or already present).")
    finally:
        db.close()
