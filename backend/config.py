import os
from dotenv import load_dotenv

load_dotenv()


def _positive_int_env(name: str, default: str) -> int:
    """Read a positive integer environment variable or fail during startup."""
    try:
        value = int(os.getenv(name, default))
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value < 1:
        raise ValueError(f"{name} must be at least 1")
    return value


SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = _positive_int_env("SMTP_PORT", "587")
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}

COMPILER_TIMEOUT_SECONDS = _positive_int_env("COMPILER_TIMEOUT_SECONDS", "5")
COMPILER_SANDBOX_ENABLED = os.getenv("COMPILER_SANDBOX_ENABLED", "false").lower() in {"1", "true", "yes"}

OTP_EXPIRY_MINUTES = _positive_int_env("OTP_EXPIRY_MINUTES", "5")
OTP_MAX_ATTEMPTS = _positive_int_env("OTP_MAX_ATTEMPTS", "5")

# Authentication abuse-protection defaults. Every limit/window is validated
# during module import so invalid deployment configuration fails fast.
AUTH_LOGIN_RATE_LIMIT = _positive_int_env("AUTH_LOGIN_RATE_LIMIT", "5")
AUTH_LOGIN_ACCOUNT_RATE_LIMIT = _positive_int_env(
    "AUTH_LOGIN_ACCOUNT_RATE_LIMIT",
    "20",
)
AUTH_LOGIN_RATE_WINDOW_SECONDS = _positive_int_env(
    "AUTH_LOGIN_RATE_WINDOW_SECONDS",
    "600",
)
AUTH_REGISTER_RATE_LIMIT = _positive_int_env(
    "AUTH_REGISTER_RATE_LIMIT",
    "10",
)
AUTH_REGISTER_RATE_WINDOW_SECONDS = _positive_int_env(
    "AUTH_REGISTER_RATE_WINDOW_SECONDS",
    "3600",
)
AUTH_OTP_REQUEST_RATE_LIMIT = _positive_int_env(
    "AUTH_OTP_REQUEST_RATE_LIMIT",
    "3",
)
AUTH_OTP_REQUEST_RATE_WINDOW_SECONDS = _positive_int_env(
    "AUTH_OTP_REQUEST_RATE_WINDOW_SECONDS",
    "900",
)
AUTH_OTP_VERIFY_RATE_LIMIT = _positive_int_env(
    "AUTH_OTP_VERIFY_RATE_LIMIT",
    str(OTP_MAX_ATTEMPTS),
)
AUTH_OTP_VERIFY_RATE_WINDOW_SECONDS = _positive_int_env(
    "AUTH_OTP_VERIFY_RATE_WINDOW_SECONDS",
    "900",
)

# Render and similar reverse-proxy deployments append the real client address
# to X-Forwarded-For. We only trust that header when the direct peer is a
# loopback/private proxy and select from the right side of the chain.
AUTH_TRUSTED_PROXY_HOPS = _positive_int_env(
    "AUTH_TRUSTED_PROXY_HOPS",
    "1",
)
