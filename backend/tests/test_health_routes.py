"""Focused tests for SkillSprint health-check endpoints."""

from __future__ import annotations

import os
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest


BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from routes import health_routes


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(
        health_routes.router,
        prefix="/health",
    )
    return TestClient(app)


def test_liveness_returns_200(client):
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "skillsprint-api",
    }


def test_readiness_returns_200_when_dependencies_are_healthy(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        health_routes,
        "check_database_readiness",
        lambda: {"status": "ok"},
    )
    monkeypatch.setattr(
        health_routes,
        "check_compiler_readiness",
        lambda: {
            "status": "ok",
            "available_languages": 9,
            "configured_languages": 9,
        },
    )

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {
            "database": {"status": "ok"},
            "compiler": {
                "status": "ok",
                "available_languages": 9,
                "configured_languages": 9,
            },
        },
    }


def test_readiness_accepts_partial_compiler_availability(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        health_routes,
        "check_database_readiness",
        lambda: {"status": "ok"},
    )
    monkeypatch.setattr(
        health_routes,
        "check_compiler_readiness",
        lambda: {
            "status": "degraded",
            "available_languages": 3,
            "configured_languages": 9,
        },
    )

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert (
        response.json()["checks"]["compiler"]["status"]
        == "degraded"
    )


def test_database_failure_returns_503_without_sensitive_details(
    client,
    monkeypatch,
):
    secret_error = (
        "postgresql://admin:super-secret@private-db.example.com/"
        "skillsprint /srv/private/database.py"
    )

    class BrokenConnection:
        def __enter__(self):
            raise RuntimeError(secret_error)

        def __exit__(self, exc_type, exc, tb):
            return False

    class BrokenEngine:
        def connect(self):
            return BrokenConnection()

    monkeypatch.setattr(health_routes, "engine", BrokenEngine())
    monkeypatch.setattr(
        health_routes,
        "check_compiler_readiness",
        lambda: {
            "status": "ok",
            "available_languages": 4,
            "configured_languages": 4,
        },
    )

    response = client.get("/health/ready")
    body = response.text

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["checks"]["database"] == {
        "status": "unavailable"
    }
    assert "super-secret" not in body
    assert "private-db.example.com" not in body
    assert "/srv/private/database.py" not in body


def test_missing_compiler_runtimes_return_503(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        health_routes,
        "check_database_readiness",
        lambda: {"status": "ok"},
    )
    monkeypatch.setattr(
        health_routes,
        "list_supported_languages",
        lambda: [
            {
                "key": "python",
                "type": "interpreted",
                "available": False,
                "missing": ["python"],
            },
            {
                "key": "cpp",
                "type": "compiled",
                "available": False,
                "missing": ["g++"],
            },
            {
                "key": "html",
                "type": "web",
                "available": True,
                "missing": [],
            },
        ],
    )

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {
            "database": {"status": "ok"},
            "compiler": {
                "status": "unavailable",
                "available_languages": 0,
                "configured_languages": 2,
            },
        },
    }


def test_compiler_check_does_not_count_web_only_languages(
    monkeypatch,
):
    monkeypatch.setattr(
        health_routes,
        "list_supported_languages",
        lambda: [
            {
                "key": "html",
                "type": "web",
                "available": True,
            },
            {
                "key": "css",
                "type": "web",
                "available": True,
            },
        ],
    )

    assert health_routes.check_compiler_readiness() == {
        "status": "unavailable",
        "available_languages": 0,
        "configured_languages": 0,
    }


def test_compiler_discovery_failure_is_sanitized(
    monkeypatch,
):
    monkeypatch.setattr(
        health_routes,
        "list_supported_languages",
        lambda: (_ for _ in ()).throw(
            RuntimeError(
                "missing /private/toolchain path "
                "token=should-not-leak"
            )
        ),
    )

    result = health_routes.check_compiler_readiness()

    assert result == {
        "status": "unavailable",
        "available_languages": 0,
        "configured_languages": 0,
    }
    assert "token" not in str(result)
    assert "/private/toolchain" not in str(result)
