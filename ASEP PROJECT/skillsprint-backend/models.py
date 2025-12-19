from sqlalchemy import Column, Integer, String, DateTime, Enum
from datetime import datetime
import enum
from database import Base

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
