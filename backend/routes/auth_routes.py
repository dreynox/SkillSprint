import hashlib
import hmac
import random
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import (
    OTP_EXPIRY_MINUTES,
    OTP_MAX_ATTEMPTS,
    SECRET_KEY,
    SMTP_FROM_EMAIL,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_TLS,
    SMTP_USER,
)
from database import get_db
from models import PasswordResetOTP, RoleEnum, User
from schemas import (
    AuthResponse,
    ForgotPasswordRequest,
    ForgotPasswordVerifyRequest,
    MessageResponse,
    UserCreate,
    UserLogin,
)
from auth import create_access_token, hash_password, verify_password

router = APIRouter()


def _generate_otp() -> str:
    return f"{random.randint(0, 999999):06d}"


def _hash_otp(email: str, otp: str) -> str:
    # Tie OTP hash to email and server secret.
    payload = f"{email.lower()}|{otp}|{SECRET_KEY}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _send_otp_email(email: str, otp: str) -> None:
    if not SMTP_HOST or not SMTP_FROM_EMAIL:
        # Dev fallback when SMTP is not configured.
        print(f"[OTP][DEV] Password reset OTP for {email}: {otp}")
        return

    subject = "SkillSprint Password Reset OTP"
    body = (
        f"Your SkillSprint OTP is: {otp}\n\n"
        f"This code expires in {OTP_EXPIRY_MINUTES} minutes."
    )
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM_EMAIL
    msg["To"] = email

    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20)
    try:
        server.ehlo()
        if SMTP_USE_TLS:
            server.starttls()
            server.ehlo()
        if SMTP_USER and SMTP_PASSWORD:
            server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM_EMAIL, [email], msg.as_string())
    finally:
        server.quit()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    normalized_email = payload.email.lower().strip()
    existing_user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    role_value = payload.role.lower().strip()
    if role_value not in {"student", "admin"}:
        role_value = "student"

    user = User(
        name=payload.name,
        email=normalized_email,
        password_hash=hash_password(payload.password),
        role=RoleEnum(role_value),
        srn=payload.srn,
        prn=payload.prn,
        year=payload.year,
        branch=payload.branch,
        division=payload.division,
        roll_no=payload.roll_no,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return AuthResponse(message="User registered successfully", user=user, token=token)


@router.post("/login", response_model=AuthResponse)
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    normalized_email = payload.email.lower().strip()
    user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return AuthResponse(message="Login successful", user=user, token=token)


@router.post("/forgot-password/request-otp", response_model=MessageResponse)
def request_forgot_password_otp(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()

    # Invalidate previous active OTPs for this email.
    active_codes = (
        db.query(PasswordResetOTP)
        .filter(PasswordResetOTP.email == email, PasswordResetOTP.consumed.is_(False))
        .all()
    )
    for code in active_codes:
        code.consumed = True
        db.add(code)

    if user:
        otp = _generate_otp()
        otp_record = PasswordResetOTP(
            email=email,
            otp_hash=_hash_otp(email, otp),
            expires_at=datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
            consumed=False,
            attempts=0,
        )
        db.add(otp_record)
        _send_otp_email(email, otp)

    db.commit()

    return MessageResponse(
        message=f'A 6-digit OTP(One-Time-Password) has been sent to you email adrress "{email}", Please verify it within 5 minutes before it expires'
    )


@router.post("/forgot-password/verify-otp", response_model=MessageResponse)
def verify_forgot_password_otp(payload: ForgotPasswordVerifyRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP or email")

    otp_record = (
        db.query(PasswordResetOTP)
        .filter(PasswordResetOTP.email == email, PasswordResetOTP.consumed.is_(False))
        .order_by(PasswordResetOTP.created_at.desc())
        .first()
    )
    if not otp_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active OTP found")

    if otp_record.expires_at < datetime.utcnow():
        otp_record.consumed = True
        db.add(otp_record)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired")

    if otp_record.attempts >= OTP_MAX_ATTEMPTS:
        otp_record.consumed = True
        db.add(otp_record)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum OTP attempts exceeded")

    submitted_hash = _hash_otp(email, payload.otp)
    if not hmac.compare_digest(submitted_hash, otp_record.otp_hash):
        otp_record.attempts += 1
        db.add(otp_record)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

    user.password_hash = hash_password(payload.new_password)
    otp_record.consumed = True
    db.add(user)
    db.add(otp_record)
    db.commit()

    return MessageResponse(message="Password reset successful. You can now login with your new password.")
