import hashlib
import hmac
import ipaddress
import logging
import random
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    status,
)
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config import (
    AUTH_LOGIN_ACCOUNT_RATE_LIMIT,
    AUTH_LOGIN_RATE_LIMIT,
    AUTH_LOGIN_RATE_WINDOW_SECONDS,
    AUTH_OTP_REQUEST_RATE_LIMIT,
    AUTH_OTP_REQUEST_RATE_WINDOW_SECONDS,
    AUTH_OTP_VERIFY_RATE_LIMIT,
    AUTH_OTP_VERIFY_RATE_WINDOW_SECONDS,
    AUTH_REGISTER_RATE_LIMIT,
    AUTH_REGISTER_RATE_WINDOW_SECONDS,
    AUTH_TRUSTED_PROXY_HOPS,
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
    RateLimitDecision,
    RateLimiter,
    build_rate_limit_key,
    normalize_identifier,
)


router = APIRouter()
logger = logging.getLogger(__name__)
rate_limiter = RateLimiter()

# Password verification is intentionally performed even when no matching user
# exists so login timing does not trivially reveal registered email addresses.
DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))

GENERIC_OTP_RESPONSE = (
    "If an account exists for that email, a password-reset OTP has been sent."
)
GENERIC_OTP_FAILURE = "Invalid or expired OTP"
GENERIC_REGISTRATION_FAILURE = "Unable to register with the provided details"


def _valid_ip(value: str) -> str | None:
    try:
        return str(ipaddress.ip_address(value.strip()))
    except ValueError:
        return None


def _peer_is_trusted_proxy(host: str) -> bool:
    """Trust proxy headers only from loopback/private platform peers."""
    if host in {"localhost", "testclient"}:
        return True
    parsed = _valid_ip(host)
    if parsed is None:
        return False
    ip = ipaddress.ip_address(parsed)
    return ip.is_private or ip.is_loopback


def _requester_ip(request: Request) -> str:
    """Resolve the requester from a validated right-to-left proxy chain.

    On Render/reverse-proxy deployments the direct peer is private/loopback.
    Only in that case do we inspect X-Forwarded-For, and we select from the
    trusted right side rather than the spoofable leftmost entry.
    """
    peer = request.client.host if request.client else ""
    forwarded = request.headers.get("x-forwarded-for", "")

    if forwarded and _peer_is_trusted_proxy(peer):
        valid_chain = [
            parsed
            for part in forwarded.split(",")
            if (parsed := _valid_ip(part)) is not None
        ]
        if len(valid_chain) >= AUTH_TRUSTED_PROXY_HOPS:
            return valid_chain[-AUTH_TRUSTED_PROXY_HOPS]

    parsed_peer = _valid_ip(peer)
    return parsed_peer or "unknown"


def _rate_limited(decision: RateLimitDecision) -> None:
    if decision.allowed:
        return
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many requests. Please try again later.",
        headers={"Retry-After": str(decision.retry_after)},
    )


from services.email_service import EmailService, get_email_service

def _generate_otp() -> str:
    return f"{random.randint(0, 999999):06d}"


def _hash_otp(email: str, otp: str) -> str:
    payload = f"{email.lower()}|{otp}|{SECRET_KEY}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _decoy_email(email: str) -> str:
    """Create a non-reversible placeholder for unknown-account work."""
    digest = hmac.new(
        SECRET_KEY.encode("utf-8"),
        normalize_identifier(email).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:32]
    return f"unknown-{digest}@invalid.local"


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
        rate_limiter.consume(
            key,
            limit=AUTH_REGISTER_RATE_LIMIT,
            window_seconds=AUTH_REGISTER_RATE_WINDOW_SECONDS,
        )
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
            detail=GENERIC_REGISTRATION_FAILURE,
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
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=GENERIC_REGISTRATION_FAILURE,
        )
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
    requester = _requester_ip(request)

    key = build_rate_limit_key(
        "login",
        requester=requester,
        identifier=normalized_email,
    )
    account_key = build_rate_limit_key(
        "login-account",
        requester="account",
        identifier=normalized_email,
    )

    _rate_limited(
        rate_limiter.check(
            key,
            limit=AUTH_LOGIN_RATE_LIMIT,
            window_seconds=AUTH_LOGIN_RATE_WINDOW_SECONDS,
        )
    )
    _rate_limited(
        rate_limiter.check(
            account_key,
            limit=AUTH_LOGIN_ACCOUNT_RATE_LIMIT,
            window_seconds=AUTH_LOGIN_RATE_WINDOW_SECONDS,
        )
    )

    user = (
        db.query(User)
        .filter(func.lower(User.email) == normalized_email)
        .first()
    )

    password_hash = (
        user.password_hash
        if user is not None
        else DUMMY_PASSWORD_HASH
    )
    password_valid = verify_password(
        payload.password,
        password_hash,
    )

    if user is None or not password_valid:
        rate_limiter.record(
            key,
            limit=AUTH_LOGIN_RATE_LIMIT,
            window_seconds=AUTH_LOGIN_RATE_WINDOW_SECONDS,
        )
        rate_limiter.record(
            account_key,
            limit=AUTH_LOGIN_ACCOUNT_RATE_LIMIT,
            window_seconds=AUTH_LOGIN_RATE_WINDOW_SECONDS,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    rate_limiter.reset(key)
    rate_limiter.reset(account_key)

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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
):
    email = normalize_identifier(payload.email)
    key = build_rate_limit_key(
        "otp-request",
        requester=_requester_ip(request),
        identifier=email,
    )
    _rate_limited(
        rate_limiter.consume(
            key,
            limit=AUTH_OTP_REQUEST_RATE_LIMIT,
            window_seconds=AUTH_OTP_REQUEST_RATE_WINDOW_SECONDS,
        )
    )

    user = db.query(User).filter(func.lower(User.email) == email).first()

    # Query active OTP state for both known and unknown accounts to reduce
    # account-existence timing differences.
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
    otp_hash = _hash_otp(email, otp)
    expires_at = datetime.utcnow() + timedelta(
        minutes=OTP_EXPIRY_MINUTES
    )

    if user is not None:
        db.add(
            PasswordResetOTP(
                email=email,
                otp_hash=otp_hash,
                expires_at=expires_at,
                consumed=False,
                attempts=0,
            )
        )
    else:
        # Perform comparable insert/delete work without persisting the unknown
        # address. The decoy identifier is HMAC-derived and non-reversible.
        decoy = PasswordResetOTP(
            email=_decoy_email(email),
            otp_hash=otp_hash,
            expires_at=expires_at,
            consumed=True,
            attempts=0,
        )
        db.add(decoy)
        db.flush()
        db.delete(decoy)

    db.commit()

    if user is not None:
        # No durable worker exists in this repository, so FastAPI BackgroundTasks
        # is the minimal non-blocking fallback recommended by the review.
        background_tasks.add_task(
            email_service.send_otp_email,
            email,
            otp,
            _decoy_email(email).split("@", 1)[0]
        )

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
