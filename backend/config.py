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

# ── Compiler / Sandbox ────────────────────────────────────────────────────────
# Set COMPILER_SANDBOX_ENABLED=true on any host that has the Docker socket
# available (/var/run/docker.sock mounted). When false the engine falls back to
# direct subprocess execution (suitable for local development only).
COMPILER_SANDBOX_ENABLED = os.getenv("COMPILER_SANDBOX_ENABLED", "false").lower() in {"1", "true", "yes"}

# Docker image used as the ephemeral execution sandbox.
# Build it with:  docker build -t skillsprint-sandbox:latest .
COMPILER_SANDBOX_IMAGE = os.getenv("COMPILER_SANDBOX_IMAGE", "skillsprint-sandbox:latest")

# Resource limits applied to every sandbox container.
COMPILER_CPU_LIMIT = os.getenv("COMPILER_CPU_LIMIT", "0.5")          # fractional CPUs
COMPILER_MEM_LIMIT = os.getenv("COMPILER_MEM_LIMIT", "256m")         # Docker memory string
COMPILER_PID_LIMIT = int(os.getenv("COMPILER_PID_LIMIT", "64"))      # max processes (blocks fork bombs)
COMPILER_TIMEOUT_SECONDS = int(os.getenv("COMPILER_TIMEOUT_SECONDS", "10"))  # hard wall-clock cap
COMPILER_NETWORK_MODE = os.getenv("COMPILER_NETWORK_MODE", "none")   # "none" = no outbound network

