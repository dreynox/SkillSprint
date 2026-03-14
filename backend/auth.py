from datetime import datetime, timedelta
import base64
import hashlib
import hmac
import os

import jwt
from config import SECRET_KEY, ALGORITHM
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import User

MAX_BCRYPT_BYTES = 72
security = HTTPBearer()
PBKDF2_ITERATIONS = 100000


def _pbkdf2_hash(password: str, salt: bytes) -> str:
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return base64.b64encode(derived).decode("utf-8")

def hash_password(password: str) -> str:
    if len(password.encode("utf-8")) > MAX_BCRYPT_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password too long. Use at most {MAX_BCRYPT_BYTES} characters.",
        )
    salt = os.urandom(16)
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    hashed = _pbkdf2_hash(password, salt)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt_b64}${hashed}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if len(plain_password.encode("utf-8")) > MAX_BCRYPT_BYTES:
        return False

    if hashed_password.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt_b64, stored_hash = hashed_password.split("$", 3)
            salt = base64.b64decode(salt_b64.encode("utf-8"))
            recalculated = hashlib.pbkdf2_hmac(
                "sha256",
                plain_password.encode("utf-8"),
                salt,
                int(iterations),
            )
            return hmac.compare_digest(
                base64.b64encode(recalculated).decode("utf-8"),
                stored_hash,
            )
        except (ValueError, TypeError):
            return False

    return False


# JWT Token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=2)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# Dependency to get current user from token
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Extract user from Bearer token in Authorization header.
    Usage: current_user: User = Depends(get_current_user)
    """
    token = credentials.credentials
    user_id = verify_token(token)
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user


# Optional: Admin-only dependency
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Require that the current user is an admin.
    Usage: admin: User = Depends(require_admin)
    """
    role_value = getattr(current_user.role, "value", str(current_user.role))
    if role_value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

