import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}

OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "5"))
OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))


# Authentication abuse-protection defaults. These can be overridden by
# environment variables without changing endpoint code.
AUTH_LOGIN_RATE_LIMIT = int(os.getenv("AUTH_LOGIN_RATE_LIMIT", "5"))
AUTH_LOGIN_RATE_WINDOW_SECONDS = int(
    os.getenv("AUTH_LOGIN_RATE_WINDOW_SECONDS", "600")
)
AUTH_REGISTER_RATE_LIMIT = int(os.getenv("AUTH_REGISTER_RATE_LIMIT", "10"))
AUTH_REGISTER_RATE_WINDOW_SECONDS = int(
    os.getenv("AUTH_REGISTER_RATE_WINDOW_SECONDS", "3600")
)
AUTH_OTP_REQUEST_RATE_LIMIT = int(
    os.getenv("AUTH_OTP_REQUEST_RATE_LIMIT", "3")
)
AUTH_OTP_REQUEST_RATE_WINDOW_SECONDS = int(
    os.getenv("AUTH_OTP_REQUEST_RATE_WINDOW_SECONDS", "900")
)
AUTH_OTP_VERIFY_RATE_LIMIT = int(
    os.getenv("AUTH_OTP_VERIFY_RATE_LIMIT", str(OTP_MAX_ATTEMPTS))
)
AUTH_OTP_VERIFY_RATE_WINDOW_SECONDS = int(
    os.getenv("AUTH_OTP_VERIFY_RATE_WINDOW_SECONDS", "900")
)
