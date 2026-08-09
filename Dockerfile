FROM python:3.11-slim

# ── Image metadata ────────────────────────────────────────────────────────────
# This image serves two roles:
#   1. Outer API server  (default)
#   2. Execution sandbox (tag as skillsprint-sandbox:latest)
#      Used by sandbox.py when COMPILER_SANDBOX_ENABLED=true.
#      Each code submission spins up a fresh, ephemeral container from this
#      image with CPU/memory/PID/network limits and a read-only filesystem.
LABEL org.opencontainers.image.title="SkillSprint" \
      org.opencontainers.image.description="SkillSprint API + multi-language sandbox" \
      skillsprint.sandbox.compatible="true"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
        gdb \
        default-jdk \
        nodejs \
        npm \
        php-cli \
        golang-go \
        rustc \
        cargo \
        r-base \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN python -m pip install --upgrade pip \
    && pip install -r /app/backend/requirements.txt

COPY . /app

# ── Non-root API user ─────────────────────────────────────────────────────────
# The outer API server runs as appuser (non-root).
# Inside the execution sandbox containers, code runs as 'nobody' (enforced by
# sandbox.py via --user nobody).
RUN groupadd --system appgroup \
    && useradd --system --gid appgroup --no-create-home appuser \
    && chown -R appuser:appgroup /app

WORKDIR /app/backend

# Create the sandbox scratch directory used by execution containers.
RUN mkdir -p /sandbox && chmod 1777 /sandbox

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]