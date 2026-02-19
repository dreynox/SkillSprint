import os
from sqlalchemy import create_engine
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
