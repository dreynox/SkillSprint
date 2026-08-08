"""Tests for authentication rate limiting and OTP abuse protection."""

from __future__ import annotations

from datetime import datetime, timedelta
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from database import Base, get_db
from models import PasswordResetOTP, RoleEnum, User
from routes import auth_routes
from services.rate_limiter import (
    InMemoryRateLimitStore,
    RateLimiter,
    build_rate_limit_key,
)


class FakeClock:
    def __init__(self, start: float = 1_700_000_000.0):
        self.value = start

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


@pytest.fixture
def app_db_clock(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)
    session = TestingSession()

    user = User(
        name="Existing User",
        email="user@example.com",
        password_hash=auth_routes.hash_password("correct-password"),
        role=RoleEnum.STUDENT,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    clock = FakeClock()
    limiter = RateLimiter(
        store=InMemoryRateLimitStore(),
        clock=clock,
    )
    monkeypatch.setattr(auth_routes, "rate_limiter", limiter)

    # Keep tests fast and deterministic.
    monkeypatch.setattr(auth_routes, "AUTH_LOGIN_RATE_LIMIT", 3)
    monkeypatch.setattr(
        auth_routes,
        "AUTH_LOGIN_RATE_WINDOW_SECONDS",
        60,
    )
    monkeypatch.setattr(auth_routes, "AUTH_REGISTER_RATE_LIMIT", 2)
    monkeypatch.setattr(
        auth_routes,
        "AUTH_REGISTER_RATE_WINDOW_SECONDS",
        60,
    )
    monkeypatch.setattr(auth_routes, "AUTH_OTP_REQUEST_RATE_LIMIT", 2)
    monkeypatch.setattr(
        auth_routes,
        "AUTH_OTP_REQUEST_RATE_WINDOW_SECONDS",
        60,
    )
    monkeypatch.setattr(auth_routes, "AUTH_OTP_VERIFY_RATE_LIMIT", 3)
    monkeypatch.setattr(
        auth_routes,
        "AUTH_OTP_VERIFY_RATE_WINDOW_SECONDS",
        60,
    )
    monkeypatch.setattr(auth_routes, "OTP_MAX_ATTEMPTS", 3)

    sent_otps = {}

    def fake_send(email, otp):
        sent_otps[email] = otp

    monkeypatch.setattr(auth_routes, "_send_otp_email", fake_send)
    monkeypatch.setattr(auth_routes, "_generate_otp", lambda: "123456")

    app = FastAPI()
    app.include_router(auth_routes.router, prefix="/auth")

    def override_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_db

    yield TestClient(app), session, clock, sent_otps, user

    session.close()
    Base.metadata.drop_all(bind=engine)


def login(client, password):
    return client.post(
        "/auth/login",
        json={
            "email": "USER@EXAMPLE.COM",
            "password": password,
        },
    )


def test_failed_logins_are_rate_limited_with_retry_after(
    app_db_clock,
):
    client, _, _, _, _ = app_db_clock

    assert login(client, "wrong-1").status_code == 401
    assert login(client, "wrong-2").status_code == 401
    third = login(client, "wrong-3")
    assert third.status_code == 401

    blocked = login(client, "wrong-4")
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) >= 1
    assert blocked.json()["detail"] == (
        "Too many requests. Please try again later."
    )


def test_successful_login_resets_failed_attempt_counter(
    app_db_clock,
):
    client, _, _, _, _ = app_db_clock

    assert login(client, "wrong-1").status_code == 401
    assert login(client, "wrong-2").status_code == 401
    assert login(client, "correct-password").status_code == 200

    # A successful login cleared the two previous failures.
    assert login(client, "wrong-again").status_code == 401
    assert login(client, "wrong-again-2").status_code == 401


def test_login_limit_resets_after_window(app_db_clock):
    client, _, clock, _, _ = app_db_clock

    for password in ("bad-1", "bad-2", "bad-3"):
        assert login(client, password).status_code == 401

    assert login(client, "blocked").status_code == 429

    clock.advance(61)

    assert login(client, "new-window").status_code == 401


def test_registration_is_limited_per_requester(app_db_clock):
    client, _, _, _, _ = app_db_clock

    first = client.post(
        "/auth/register",
        json={
            "name": "One",
            "email": "one@example.com",
            "password": "password1",
        },
    )
    assert first.status_code == 201

    second = client.post(
        "/auth/register",
        json={
            "name": "Two",
            "email": "two@example.com",
            "password": "password2",
        },
    )
    assert second.status_code == 201

    blocked = client.post(
        "/auth/register",
        json={
            "name": "Three",
            "email": "three@example.com",
            "password": "password3",
        },
    )
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers


def test_otp_request_does_not_reveal_account_existence(
    app_db_clock,
):
    client, _, _, _, _ = app_db_clock

    existing = client.post(
        "/auth/forgot-password/request-otp",
        json={"email": "user@example.com"},
    )
    missing = client.post(
        "/auth/forgot-password/request-otp",
        json={"email": "missing@example.com"},
    )

    assert existing.status_code == 200
    assert missing.status_code == 200
    assert existing.json() == missing.json()
    assert "exists" in existing.json()["message"].lower()


def test_otp_requests_are_limited_per_email_and_requester(
    app_db_clock,
):
    client, _, _, _, _ = app_db_clock

    for _ in range(2):
        response = client.post(
            "/auth/forgot-password/request-otp",
            json={"email": "user@example.com"},
        )
        assert response.status_code == 200

    blocked = client.post(
        "/auth/forgot-password/request-otp",
        json={"email": "user@example.com"},
    )
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers

    # Different identifier gets a separate bucket for the same requester.
    other = client.post(
        "/auth/forgot-password/request-otp",
        json={"email": "different@example.com"},
    )
    assert other.status_code == 200


def test_invalid_otp_attempts_consume_and_exhaust_record(
    app_db_clock,
):
    client, session, _, _, _ = app_db_clock

    request_response = client.post(
        "/auth/forgot-password/request-otp",
        json={"email": "user@example.com"},
    )
    assert request_response.status_code == 200

    for attempt in range(2):
        response = client.post(
            "/auth/forgot-password/verify-otp",
            json={
                "email": "user@example.com",
                "otp": "000000",
                "new_password": "new-password",
            },
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid or expired OTP"

    third = client.post(
        "/auth/forgot-password/verify-otp",
        json={
            "email": "user@example.com",
            "otp": "000000",
            "new_password": "new-password",
        },
    )
    assert third.status_code == 429
    assert "Retry-After" in third.headers

    record = (
        session.query(PasswordResetOTP)
        .filter(PasswordResetOTP.email == "user@example.com")
        .order_by(PasswordResetOTP.created_at.desc())
        .first()
    )
    session.refresh(record)
    assert record.attempts == 3
    assert record.consumed is True


def test_successful_otp_resets_verification_rate_limit(
    app_db_clock,
):
    client, _, _, _, _ = app_db_clock

    assert client.post(
        "/auth/forgot-password/request-otp",
        json={"email": "user@example.com"},
    ).status_code == 200

    assert client.post(
        "/auth/forgot-password/verify-otp",
        json={
            "email": "user@example.com",
            "otp": "000000",
            "new_password": "new-password",
        },
    ).status_code == 400

    success = client.post(
        "/auth/forgot-password/verify-otp",
        json={
            "email": "user@example.com",
            "otp": "123456",
            "new_password": "new-password",
        },
    )
    assert success.status_code == 200

    # Request a fresh OTP and verify that the previous bad-attempt bucket was
    # cleared by success.
    assert client.post(
        "/auth/forgot-password/request-otp",
        json={"email": "user@example.com"},
    ).status_code == 200

    failed_again = client.post(
        "/auth/forgot-password/verify-otp",
        json={
            "email": "user@example.com",
            "otp": "000000",
            "new_password": "newer-password",
        },
    )
    assert failed_again.status_code == 400


def test_missing_user_and_missing_otp_use_same_generic_error(
    app_db_clock,
):
    client, _, _, _, _ = app_db_clock

    missing_user = client.post(
        "/auth/forgot-password/verify-otp",
        json={
            "email": "missing@example.com",
            "otp": "123456",
            "new_password": "new-password",
        },
    )

    no_active_otp = client.post(
        "/auth/forgot-password/verify-otp",
        json={
            "email": "user@example.com",
            "otp": "123456",
            "new_password": "new-password",
        },
    )

    assert missing_user.status_code == 400
    assert no_active_otp.status_code == 400
    assert missing_user.json()["detail"] == "Invalid or expired OTP"
    assert missing_user.json() == no_active_otp.json()


def test_rate_limit_key_does_not_contain_raw_email():
    key = build_rate_limit_key(
        "login",
        requester="127.0.0.1",
        identifier="User@Example.com",
    )

    assert "user@example.com" not in key.lower()
    assert key.startswith("login:")
