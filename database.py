from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# For local development, use SQLite
DATABASE_URL = "sqlite:///./skillsprint.db"

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
