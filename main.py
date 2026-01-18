from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from models import User, RoleEnum
from auth import hash_password, verify_password, create_access_token


# ---------- APP & DATABASE SETUP ----------

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SkillSprint API",
    description="Competitive Coding and Hackathon Portal",
    version="1.0.0",
)

# CORS: allow GitHub Pages + local dev
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "https://dreynox.github.io",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
def read_root():
    return {
        "message": "SkillSprint API is running",
        "version": "1.0.0",
    }


# ---------- SCHEMAS ----------

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    year: Optional[int] = None
    branch: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    year: Optional[int] = None
    branch: Optional[str] = None
    role: RoleEnum

    class Config:
        from_attributes = True  # pydantic v2 + SQLAlchemy


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ---------- AUTH ENDPOINTS ----------

@app.post("/auth/register", response_model=AuthResponse)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    # check if email already exists
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # create user
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        year=payload.year,
        branch=payload.branch,
        role=RoleEnum.STUDENT,  # default role
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # create token
    token = create_access_token({"sub": str(user.id), "role": user.role})

    return AuthResponse(
        access_token=token,
        user=user,
    )


@app.post("/auth/login", response_model=AuthResponse)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    # find user
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # create token
    token = create_access_token({"sub": str(user.id), "role": user.role})

    return AuthResponse(
        access_token=token,
        user=user,
    )

