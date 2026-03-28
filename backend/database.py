import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

# For local development, use SQLite with absolute path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'skillsprint.db')}".replace("\\", "/")

# For production, use: DATABASE_URL = "postgresql://user:password@localhost/skillsprint"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
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
            if "year" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN year INTEGER"))
            if "branch" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN branch VARCHAR"))
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
