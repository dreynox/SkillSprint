FROM python:3.11-slim

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

WORKDIR /app/backend

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]