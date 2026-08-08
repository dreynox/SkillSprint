import hashlib
import hmac
import random
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import (
    AUTH_LOGIN_RATE_LIMIT,
    AUTH_LOGIN_RATE_WINDOW_SECONDS,
    AUTH_OTP_REQUEST_RATE_LIMIT,
    AUTH_OTP_REQUEST_RATE_WINDOW_SECONDS,
    AUTH_OTP_VERIFY_RATE_LIMIT,
    AUTH_OTP_VERIFY_RATE_WINDOW_SECONDS,
    AUTH_REGISTER_RATE_LIMIT,
    AUTH_REGISTER_RATE_WINDOW_SECONDS,
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
from services.rate_limiter import (
    RateLimiter,
    build_rate_limit_key,
    normalize_identifier,
)


router = APIRouter()
rate_limiter = RateLimiter()

GENERIC_OTP_RESPONSE = (
    "If an account exists for that email, a password-reset OTP has been sent."
)
GENERIC_OTP_FAILURE = "Invalid or expired OTP"


def _requester_ip(request: Request) -> str:
    """Return the direct peer address without trusting spoofable forwarding headers."""
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _rate_limited(decision) -> None:
    if decision.allowed:
        return
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many requests. Please try again later.",
        headers={"Retry-After": str(decision.retry_after)},
    )


def _generate_otp() -> str:
    return f"{random.randint(0, 999999):06d}"


def _hash_otp(email: str, otp: str) -> str:
    payload = f"{email.lower()}|{otp}|{SECRET_KEY}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _send_otp_email(email: str, otp: str) -> None:
    if not SMTP_HOST or not SMTP_FROM_EMAIL:
        # Dev fallback retained for local development only.
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


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    requester = _requester_ip(request)
    key = build_rate_limit_key("register", requester=requester)
    _rate_limited(
        rate_limiter.check(
            key,
            limit=AUTH_REGISTER_RATE_LIMIT,
            window_seconds=AUTH_REGISTER_RATE_WINDOW_SECONDS,
        )
    )
    # Registration is a sensitive action, so every request consumes capacity.
    rate_limiter.record(
        key,
        limit=AUTH_REGISTER_RATE_LIMIT,
        window_seconds=AUTH_REGISTER_RATE_WINDOW_SECONDS,
    )

    normalized_email = normalize_identifier(payload.email)
    existing_user = (
        db.query(User)
        .filter(func.lower(User.email) == normalized_email)
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to register with the provided details",
        )

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

    token = create_access_token(
        {"sub": str(user.id), "role": user.role.value}
    )
    return AuthResponse(
        message="User registered successfully",
        user=user,
        token=token,
    )


@router.post("/login", response_model=AuthResponse)
def login_user(
    payload: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    normalized_email = normalize_identifier(payload.email)
    key = build_rate_limit_key(
        "login",
        requester=_requester_ip(request),
        identifier=normalized_email,
    )

    _rate_limited(
        rate_limiter.check(
            key,
            limit=AUTH_LOGIN_RATE_LIMIT,
            window_seconds=AUTH_LOGIN_RATE_WINDOW_SECONDS,
        )
    )

    user = (
        db.query(User)
        .filter(func.lower(User.email) == normalized_email)
        .first()
    )
    if not user or not verify_password(
        payload.password,
        user.password_hash,
    ):
        rate_limiter.record(
            key,
            limit=AUTH_LOGIN_RATE_LIMIT,
            window_seconds=AUTH_LOGIN_RATE_WINDOW_SECONDS,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # A valid login clears previous failed-attempt state.
    rate_limiter.reset(key)

    token = create_access_token(
        {"sub": str(user.id), "role": user.role.value}
    )
    return AuthResponse(
        message="Login successful",
        user=user,
        token=token,
    )


@router.post(
    "/forgot-password/request-otp",
    response_model=MessageResponse,
)
def request_forgot_password_otp(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    email = normalize_identifier(payload.email)
    key = build_rate_limit_key(
        "otp-request",
        requester=_requester_ip(request),
        identifier=email,
    )

    _rate_limited(
        rate_limiter.check(
            key,
            limit=AUTH_OTP_REQUEST_RATE_LIMIT,
            window_seconds=AUTH_OTP_REQUEST_RATE_WINDOW_SECONDS,
        )
    )
    # Count requests whether or not the account exists to keep observable
    # behavior consistent and prevent enumeration.
    rate_limiter.record(
        key,
        limit=AUTH_OTP_REQUEST_RATE_LIMIT,
        window_seconds=AUTH_OTP_REQUEST_RATE_WINDOW_SECONDS,
    )

    user = db.query(User).filter(func.lower(User.email) == email).first()

    if user:
        active_codes = (
            db.query(PasswordResetOTP)
            .filter(
                PasswordResetOTP.email == email,
                PasswordResetOTP.consumed.is_(False),
            )
            .all()
        )
        for code in active_codes:
            code.consumed = True
            db.add(code)

        otp = _generate_otp()
        otp_record = PasswordResetOTP(
            email=email,
            otp_hash=_hash_otp(email, otp),
            expires_at=datetime.utcnow()
            + timedelta(minutes=OTP_EXPIRY_MINUTES),
            consumed=False,
            attempts=0,
        )
        db.add(otp_record)
        db.commit()
        _send_otp_email(email, otp)

    return MessageResponse(message=GENERIC_OTP_RESPONSE)


@router.post(
    "/forgot-password/verify-otp",
    response_model=MessageResponse,
)
def verify_forgot_password_otp(
    payload: ForgotPasswordVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    email = normalize_identifier(payload.email)
    key = build_rate_limit_key(
        "otp-verify",
        requester=_requester_ip(request),
        identifier=email,
    )

    _rate_limited(
        rate_limiter.check(
            key,
            limit=AUTH_OTP_VERIFY_RATE_LIMIT,
            window_seconds=AUTH_OTP_VERIFY_RATE_WINDOW_SECONDS,
        )
    )

    user = db.query(User).filter(func.lower(User.email) == email).first()
    otp_record = (
        db.query(PasswordResetOTP)
        .filter(
            PasswordResetOTP.email == email,
            PasswordResetOTP.consumed.is_(False),
        )
        .order_by(PasswordResetOTP.created_at.desc())
        .first()
    )

    now = datetime.utcnow()
    invalid = user is None or otp_record is None

    if otp_record is not None and otp_record.expires_at < now:
        otp_record.consumed = True
        db.add(otp_record)
        db.commit()
        invalid = True

    if otp_record is not None and otp_record.attempts >= OTP_MAX_ATTEMPTS:
        otp_record.consumed = True
        db.add(otp_record)
        db.commit()
        invalid = True

    if invalid:
        rate_limiter.record(
            key,
            limit=AUTH_OTP_VERIFY_RATE_LIMIT,
            window_seconds=AUTH_OTP_VERIFY_RATE_WINDOW_SECONDS,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=GENERIC_OTP_FAILURE,
        )

    submitted_hash = _hash_otp(email, payload.otp)
    if not hmac.compare_digest(
        submitted_hash,
        otp_record.otp_hash,
    ):
        otp_record.attempts += 1
        if otp_record.attempts >= OTP_MAX_ATTEMPTS:
            otp_record.consumed = True
        db.add(otp_record)
        db.commit()

        decision = rate_limiter.record(
            key,
            limit=AUTH_OTP_VERIFY_RATE_LIMIT,
            window_seconds=AUTH_OTP_VERIFY_RATE_WINDOW_SECONDS,
        )
        if not decision.allowed:
            _rate_limited(decision)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=GENERIC_OTP_FAILURE,
        )

    user.password_hash = hash_password(payload.new_password)
    otp_record.consumed = True
    db.add(user)
    db.add(otp_record)
    db.commit()

    rate_limiter.reset(key)

    return MessageResponse(
        message=(
            "Password reset successful. "
            "You can now login with your new password."
        )
    )
