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
