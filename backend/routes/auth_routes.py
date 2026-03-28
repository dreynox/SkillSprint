from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import RoleEnum, User
from schemas import AuthResponse, UserCreate, UserLogin
from auth import create_access_token, hash_password, verify_password

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    role_value = payload.role.lower().strip()
    if role_value not in {"student", "admin"}:
        role_value = "student"

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=RoleEnum(role_value),
        year=payload.year,
        branch=payload.branch,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return AuthResponse(message="User registered successfully", user=user, token=token)


@router.post("/login", response_model=AuthResponse)
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return AuthResponse(message="Login successful", user=user, token=token)
