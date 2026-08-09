import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _resolve_database_url() -> str:
    raw_database_url = os.getenv("DATABASE_URL")
    if raw_database_url:
        normalized_url = raw_database_url.replace("postgres://", "postgresql://", 1)
        return normalized_url.replace("postgresql://", "postgresql+psycopg://", 1)

    sqlite_path = os.path.join(BASE_DIR, "skillsprint.db").replace("\\", "/")
    return f"sqlite:///{sqlite_path}"


DATABASE_URL = _resolve_database_url()

engine_kwargs = {
    "connect_args": {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    "pool_pre_ping": not DATABASE_URL.startswith("sqlite"),
}

if not DATABASE_URL.startswith("sqlite"):
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(
    DATABASE_URL,
    **engine_kwargs,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_sqlite_compatibility():
    with engine.begin() as connection:
        inspector = inspect(connection)
        tables = set(inspector.get_table_names())

        if "contest_problems" in tables:
            columns = {column["name"] for column in inspector.get_columns("contest_problems")}
            if "tags" not in columns:
                connection.execute(text("ALTER TABLE contest_problems ADD COLUMN tags VARCHAR"))

        if "users" in tables:
            user_columns = {column["name"] for column in inspector.get_columns("users")}
            if "srn" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN srn VARCHAR"))
            if "prn" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN prn VARCHAR"))
            if "year" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN year INTEGER"))
            if "branch" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN branch VARCHAR"))
            if "division" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN division VARCHAR"))
            if "roll_no" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN roll_no VARCHAR"))
            if "domain" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN domain VARCHAR"))
            if "subject" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN subject VARCHAR"))
            if "bio" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN bio TEXT"))
            if "avatar_url" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR"))
            if "is_premium" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN is_premium BOOLEAN DEFAULT FALSE"))
            if "premium_expires_at" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN premium_expires_at DATETIME"))
            if "extra_xp" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN extra_xp INTEGER DEFAULT 0"))

        if "questions" in tables:
            question_columns = {column["name"] for column in inspector.get_columns("questions")}
            if "explanation" not in question_columns:
                connection.execute(text("ALTER TABLE questions ADD COLUMN explanation TEXT"))

        if "messages" in tables:
            message_columns = {column["name"] for column in inspector.get_columns("messages")}
            if "expires_at" not in message_columns:
                connection.execute(text("ALTER TABLE messages ADD COLUMN expires_at DATETIME"))

        if "contest_submissions" in tables:
            submission_columns = {column["name"] for column in inspector.get_columns("contest_submissions")}
            if "verdict" not in submission_columns:
                connection.execute(text("ALTER TABLE contest_submissions ADD COLUMN verdict VARCHAR DEFAULT 'PENDING'"))
            if "score" not in submission_columns:
                connection.execute(text("ALTER TABLE contest_submissions ADD COLUMN score INTEGER DEFAULT 0"))
            if "execution_results" not in submission_columns:
                connection.execute(text("ALTER TABLE contest_submissions ADD COLUMN execution_results TEXT"))
            if "submitted_at" not in submission_columns:
                connection.execute(text("ALTER TABLE contest_submissions ADD COLUMN submitted_at DATETIME"))


_INDEX_INITIALIZATION_LOCK_KEY = "skillsprint:index-initialization"


def _declared_composite_indexes():
    """Return the explicitly declared composite indexes managed at startup."""
    from models import (
        ContestSubmission,
        Message,
        PasswordResetOTP,
        QuizSubmission,
    )

    tables = (
        QuizSubmission.__table__,
        ContestSubmission.__table__,
        Message.__table__,
        PasswordResetOTP.__table__,
    )

    indexes = []
    for table in tables:
        for index in sorted(table.indexes, key=lambda item: item.name or ""):
            if (
                index.name
                and index.name.startswith("ix_")
                and len(index.columns) >= 2
            ):
                indexes.append(index)
    return tuple(indexes)


def _create_index_if_not_exists_sql(index, dialect) -> str:
    """Render CREATE INDEX IF NOT EXISTS with dialect-safe identifier quoting."""
    quote = dialect.identifier_preparer.quote
    index_name = quote(index.name)
    table_name = quote(index.table.name)
    columns = ", ".join(quote(column.name) for column in index.columns)
    unique = "UNIQUE " if index.unique else ""
    return (
        f"CREATE {unique}INDEX IF NOT EXISTS {index_name} "
        f"ON {table_name} ({columns})"
    )


def _acquire_postgresql_index_lock(connection) -> None:
    """Serialize index initialization across concurrent PostgreSQL workers."""
    if connection.dialect.name != "postgresql":
        return

    connection.exec_driver_sql(
        "SELECT pg_advisory_xact_lock("
        "hashtext('skillsprint:index-initialization'))"
    )


def ensure_database_indexes(bind=None):
    """Create missing declared indexes and propagate schema failures.

    PostgreSQL workers are serialized with a transaction-scoped advisory lock.
    PostgreSQL and SQLite use ``CREATE INDEX IF NOT EXISTS`` so repeated
    initialization is idempotent.
    """
    target_bind = bind or engine
    indexes = _declared_composite_indexes()

    with target_bind.begin() as connection:
        _acquire_postgresql_index_lock(connection)

        inspector = inspect(connection)
        existing_tables = set(inspector.get_table_names())

        for index in indexes:
            if index.table.name not in existing_tables:
                continue
            connection.exec_driver_sql(
                _create_index_if_not_exists_sql(
                    index,
                    connection.dialect,
                )
            )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
