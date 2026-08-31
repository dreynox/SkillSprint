"""Tests for authentication rate limiting and OTP abuse protection."""

from __future__ import annotations

import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from database import Base
from models import PasswordResetOTP, RoleEnum, User
from container import Container
from dependency_injector import providers
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
    store = InMemoryRateLimitStore()
    limiter = RateLimiter(
        store=store,
        clock=clock,
        prune_every=2,
    )
    monkeypatch.setattr(auth_routes, "rate_limiter", limiter)
    monkeypatch.setattr(auth_routes, "AUTH_LOGIN_RATE_LIMIT", 3)
    monkeypatch.setattr(
        auth_routes,
        "AUTH_LOGIN_ACCOUNT_RATE_LIMIT",
        6,
    )
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

    container = Container()
    container.wire(modules=[auth_routes])
    
    def override_db():
        yield session
        
    container.db_session.override(providers.Resource(override_db))
    app.container = container

    yield app, session, clock, sent_otps, user, store

    container.db_session.reset_override()
    container.shutdown_resources()
    container.unwire()

    session.close()
    Base.metadata.drop_all(bind=engine)


def make_client(app, requester: str = "203.0.113.10"):
    # TestClient's direct peer is "testclient", which the route treats as a
    # trusted local proxy. The rightmost XFF value exercises the production path.
    return TestClient(
        app,
        headers={"X-Forwarded-For": requester},
    )


def login(client, password, email="USER@EXAMPLE.COM"):
    return client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def test_failed_logins_are_rate_limited_with_exact_retry_after(
    app_db_clock,
):
    app, *_ = app_db_clock
    client = make_client(app)

    assert login(client, "wrong-1").status_code == 401
    assert login(client, "wrong-2").status_code == 401
    assert login(client, "wrong-3").status_code == 401

    blocked = login(client, "wrong-4")
    assert blocked.status_code == 429
    assert blocked.headers["Retry-After"] == "60"
    assert blocked.json()["detail"] == (
        "Too many requests. Please try again later."
    )


def test_successful_login_resets_requester_and_account_buckets(
    app_db_clock,
):
    app, *_ = app_db_clock
    client = make_client(app)

    assert login(client, "wrong-1").status_code == 401
    assert login(client, "wrong-2").status_code == 401
    assert login(client, "correct-password").status_code == 200

    assert login(client, "wrong-again").status_code == 401
    assert login(client, "wrong-again-2").status_code == 401


def test_account_limit_blocks_distributed_requesters(app_db_clock):
    app, *_ = app_db_clock

    for index in range(6):
        client = make_client(app, f"203.0.113.{index + 1}")
        assert login(
            client,
            f"wrong-{index}",
        ).status_code == 401

    seventh = make_client(app, "203.0.113.200")
    assert login(seventh, "wrong-7").status_code == 429


def test_unknown_user_still_runs_password_verification(
    app_db_clock,
    monkeypatch,
):
    app, *_ = app_db_clock
    client = make_client(app)
    calls = []
    original = auth_routes.verify_password

    def tracking_verify(password, password_hash):
        calls.append(password_hash)
        return original(password, password_hash)

    monkeypatch.setattr(auth_routes, "verify_password", tracking_verify)

    response = login(
        client,
        "wrong-password",
        email="unknown@example.com",
    )

    assert response.status_code == 401
    assert calls == [auth_routes.DUMMY_PASSWORD_HASH]


def test_login_limit_resets_after_window(app_db_clock):
    app, _, clock, *_ = app_db_clock
    client = make_client(app)

    for password in ("bad-1", "bad-2", "bad-3"):
        assert login(client, password).status_code == 401
    assert login(client, "blocked").status_code == 429

    clock.advance(61)

    assert login(client, "new-window").status_code == 401


def test_registration_same_requester_exhausts_but_other_is_independent(
    app_db_clock,
):
    app, *_ = app_db_clock
    client_a = make_client(app, "203.0.113.10")

    for name, email in (
        ("One", "one@example.com"),
        ("Two", "two@example.com"),
    ):
        assert client_a.post(
            "/auth/register",
            json={
                "name": name,
                "email": email,
                "password": "password1",
            },
        ).status_code == 201

    blocked = client_a.post(
        "/auth/register",
        json={
            "name": "Three",
            "email": "three@example.com",
            "password": "password3",
        },
    )
    assert blocked.status_code == 429

    client_b = make_client(app, "198.51.100.20")
    independent = client_b.post(
        "/auth/register",
        json={
            "name": "Four",
            "email": "four@example.com",
            "password": "password4",
        },
    )
    assert independent.status_code == 201


def test_registration_rolls_back_integrity_conflict(
    app_db_clock,
    monkeypatch,
):
    app, session, *_ = app_db_clock
    client = make_client(app)

    original_commit = session.commit
    calls = {"rollback": 0}

    def failing_commit():
        raise IntegrityError(
            "INSERT",
            {},
            Exception("duplicate email"),
        )

    def tracking_rollback():
        calls["rollback"] += 1
        session.expire_all()

    monkeypatch.setattr(session, "commit", failing_commit)
    monkeypatch.setattr(session, "rollback", tracking_rollback)

    response = client.post(
        "/auth/register",
        json={
            "name": "Race",
            "email": "race@example.com",
            "password": "password1",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        auth_routes.GENERIC_REGISTRATION_FAILURE
    )
    assert calls["rollback"] == 1

    monkeypatch.setattr(session, "commit", original_commit)


def test_otp_request_does_not_reveal_account_existence(
    app_db_clock,
):
    app, *_ = app_db_clock
    existing_client = make_client(app, "203.0.113.30")
    missing_client = make_client(app, "203.0.113.31")

    existing = existing_client.post(
        "/auth/forgot-password/request-otp",
        json={"email": "user@example.com"},
    )
    missing = missing_client.post(
        "/auth/forgot-password/request-otp",
        json={"email": "missing@example.com"},
    )

    assert existing.status_code == 200
    assert missing.status_code == 200
    assert existing.json() == missing.json()


def test_otp_requests_use_requester_and_email_bucket(
    app_db_clock,
):
    app, *_ = app_db_clock
    client_a = make_client(app, "203.0.113.40")

    for _ in range(2):
        response = client_a.post(
            "/auth/forgot-password/request-otp",
            json={"email": "user@example.com"},
        )
        assert response.status_code == 200

    blocked = client_a.post(
        "/auth/forgot-password/request-otp",
        json={"email": "user@example.com"},
    )
    assert blocked.status_code == 429

    # Same normalized email from a distinct real requester gets its own bucket.
    client_b = make_client(app, "198.51.100.41")
    independent = client_b.post(
        "/auth/forgot-password/request-otp",
        json={"email": "USER@EXAMPLE.COM"},
    )
    assert independent.status_code == 200


def test_forwarded_for_uses_rightmost_trusted_address(
    app_db_clock,
):
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [
            (
                b"x-forwarded-for",
                b"1.2.3.4, 198.51.100.77",
            )
        ],
        "client": ("127.0.0.1", 50000),
        "server": ("testserver", 80),
        "scheme": "http",
        "query_string": b"",
        "root_path": "",
        "http_version": "1.1",
    }
    request = Request(scope)

    # A spoofed leftmost entry should not choose 1.2.3.4.
    assert auth_routes._requester_ip(request) == "198.51.100.77"


def test_invalid_otp_attempts_consume_and_exhaust_record(
    app_db_clock,
):
    app, session, *_ = app_db_clock
    client = make_client(app)

    assert client.post(
        "/auth/forgot-password/request-otp",
        json={"email": "user@example.com"},
    ).status_code == 200

    for _ in range(2):
        response = client.post(
            "/auth/forgot-password/verify-otp",
            json={
                "email": "user@example.com",
                "otp": "000000",
                "new_password": "new-password",
            },
        )
        assert response.status_code == 400

    third = client.post(
        "/auth/forgot-password/verify-otp",
        json={
            "email": "user@example.com",
            "otp": "000000",
            "new_password": "new-password",
        },
    )
    assert third.status_code == 429
    assert third.headers["Retry-After"] == "60"

    record = (
        session.query(PasswordResetOTP)
        .filter(PasswordResetOTP.email == "user@example.com")
        .order_by(PasswordResetOTP.created_at.desc())
        .first()
    )
    session.refresh(record)
    assert record.attempts == 3
    assert record.consumed is True


def test_successful_otp_resets_http_verification_bucket(
    app_db_clock,
):
    app, *_ = app_db_clock
    client = make_client(app)

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


def test_rate_limit_key_is_hmac_and_contains_no_raw_identifier():
    key = build_rate_limit_key(
        "login",
        requester="127.0.0.1",
        identifier="User@Example.com",
    )

    assert "user@example.com" not in key.lower()
    assert "127.0.0.1" not in key
    assert key.startswith("login:")
    assert len(key.split(":", 1)[1]) == 64


def test_in_memory_store_prunes_expired_unique_keys():
    clock = FakeClock()
    store = InMemoryRateLimitStore()
    limiter = RateLimiter(
        store=store,
        clock=clock,
        prune_every=2,
    )

    assert limiter.consume(
        "one",
        limit=2,
        window_seconds=10,
    ).allowed
    clock.advance(11)

    # The second recorded action triggers periodic pruning.
    assert limiter.consume(
        "two",
        limit=2,
        window_seconds=10,
    ).allowed

    assert store.get("one") is None
    assert store.get("two") is not None


def test_consume_atomically_allows_limit_then_blocks_next():
    clock = FakeClock()
    limiter = RateLimiter(clock=clock, prune_every=100)

    first = limiter.consume("atomic", limit=2, window_seconds=60)
    second = limiter.consume("atomic", limit=2, window_seconds=60)
    third = limiter.consume("atomic", limit=2, window_seconds=60)

    assert first.allowed is True
    assert second.allowed is True
    assert second.remaining == 0
    assert third.allowed is False
    assert third.retry_after == 60
