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
    if not DATABASE_URL.startswith("sqlite"):
        return

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
            if "bio" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN bio TEXT"))
            if "avatar_url" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
