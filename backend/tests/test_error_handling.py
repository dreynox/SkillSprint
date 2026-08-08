"""Tests for request IDs and the backend error-response contract."""

from __future__ import annotations

import json
import logging
import os
import re
import sys

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.testclient import TestClient
import pytest


BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from exceptions import install_exception_handlers
from middleware.request_context import (
    REQUEST_ID_HEADER,
    RequestContextMiddleware,
)


security = HTTPBearer()


def create_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)
    install_exception_handlers(app)

    @app.get("/ok")
    def ok():
        return {"status": "ok"}

    @app.get("/validation")
    def validation(timeout: int = Query(..., ge=1, le=30)):
        return {"timeout": timeout}

    @app.get("/protected")
    def protected(
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ):
        del credentials
        return {"ok": True}

    @app.get("/missing")
    def missing():
        raise HTTPException(status_code=404, detail="Contest not found")

    @app.get("/forbidden")
    def forbidden():
        raise HTTPException(status_code=403, detail="Admin access required")

    @app.get("/service-failure")
    def service_failure():
        raise HTTPException(
            status_code=500,
            detail=(
                "database password=super-secret "
                "token=abc123 /srv/private/db.py"
            ),
        )

    @app.get("/unexpected")
    def unexpected():
        secret = "code=print('private') password=super-secret"
        raise RuntimeError(secret)

    return app


@pytest.fixture
def client():
    return TestClient(
        create_test_app(),
        raise_server_exceptions=False,
    )


def assert_error_envelope(response, *, code, message, status_code):
    assert response.status_code == status_code
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == code
    assert body["error"]["message"] == message
    assert body["error"]["request_id"] == response.headers[
        REQUEST_ID_HEADER
    ]
    return body["error"]


def test_success_response_gets_generated_request_id(client):
    response = client.get("/ok")

    assert response.status_code == 200
    request_id = response.headers[REQUEST_ID_HEADER]
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-"
        r"[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        request_id,
    )


def test_valid_provided_request_id_is_preserved(client):
    provided = "client-request-2026-0001"
    response = client.get(
        "/ok",
        headers={REQUEST_ID_HEADER: provided},
    )

    assert response.headers[REQUEST_ID_HEADER] == provided


@pytest.mark.parametrize(
    "invalid_id",
    [
        "short",
        "contains spaces",
        "line\nbreak-value",
        "x" * 129,
    ],
)
def test_invalid_request_id_is_replaced(client, invalid_id):
    response = client.get(
        "/ok",
        headers={REQUEST_ID_HEADER: invalid_id},
    )

    request_id = response.headers[REQUEST_ID_HEADER]
    assert request_id != invalid_id
    assert len(request_id) == 36


def test_validation_errors_include_safe_field_details(client):
    response = client.get(
        "/validation?timeout=31",
        headers={REQUEST_ID_HEADER: "validation-request-001"},
    )

    error = assert_error_envelope(
        response,
        code="VALIDATION_ERROR",
        message="Request validation failed",
        status_code=422,
    )
    assert error["details"] == [
        {
            "field": "timeout",
            "message": "Input should be less than or equal to 30",
        }
    ]
    assert "31" not in json.dumps(error["details"])


def test_authentication_error_uses_consistent_envelope(client):
    response = client.get(
        "/protected",
        headers={REQUEST_ID_HEADER: "auth-request-0001"},
    )

    error = assert_error_envelope(
        response,
        code="AUTHENTICATION_REQUIRED",
        message="Not authenticated",
        status_code=401,
    )
    assert error["details"] is None


def test_not_found_preserves_status_and_message(client):
    response = client.get(
        "/missing",
        headers={REQUEST_ID_HEADER: "missing-request-01"},
    )

    assert_error_envelope(
        response,
        code="RESOURCE_NOT_FOUND",
        message="Contest not found",
        status_code=404,
    )


def test_forbidden_preserves_status_and_message(client):
    response = client.get("/forbidden")

    assert_error_envelope(
        response,
        code="FORBIDDEN",
        message="Admin access required",
        status_code=403,
    )


def test_http_500_detail_is_not_exposed(client):
    response = client.get(
        "/service-failure",
        headers={REQUEST_ID_HEADER: "server-http-error-01"},
    )

    error = assert_error_envelope(
        response,
        code="INTERNAL_ERROR",
        message="Internal server error",
        status_code=500,
    )
    serialized = json.dumps(error)
    assert "super-secret" not in serialized
    assert "abc123" not in serialized
    assert "/srv/private/db.py" not in serialized


def test_unexpected_exception_returns_safe_500_with_header(client):
    response = client.get(
        "/unexpected",
        headers={REQUEST_ID_HEADER: "unexpected-request-01"},
    )

    error = assert_error_envelope(
        response,
        code="INTERNAL_ERROR",
        message="Internal server error",
        status_code=500,
    )
    serialized = json.dumps(error)
    assert "private" not in serialized
    assert "super-secret" not in serialized
    assert error["details"] is None


def test_logs_include_same_request_id(client, caplog):
    with caplog.at_level(
        logging.INFO,
        logger="skillsprint.errors",
    ):
        response = client.get(
            "/missing",
            headers={REQUEST_ID_HEADER: "trace-request-0001"},
        )

    matching = [
        record
        for record in caplog.records
        if record.name == "skillsprint.errors"
        and getattr(record, "request_id", None)
        == response.headers[REQUEST_ID_HEADER]
    ]
    assert matching
    assert matching[-1].status_code == 404


def test_unexpected_log_has_safe_stack_without_secret_text(
    client,
    caplog,
):
    with caplog.at_level(
        logging.ERROR,
        logger="skillsprint.errors",
    ):
        response = client.get(
            "/unexpected",
            headers={REQUEST_ID_HEADER: "traceback-request-01"},
        )

    assert response.status_code == 500
    matching = [
        record
        for record in caplog.records
        if record.name == "skillsprint.errors"
        and getattr(record, "event", None)
        == "unhandled_exception"
    ]
    assert matching

    record = matching[-1]
    assert record.request_id == response.headers[REQUEST_ID_HEADER]
    assert record.exception_type == "RuntimeError"
    assert record.stack_trace
    assert all(
        set(frame) == {"file", "line", "function"}
        for frame in record.stack_trace
    )

    logged = json.dumps(
        {
            "message": record.getMessage(),
            "exception_type": record.exception_type,
            "stack_trace": record.stack_trace,
        }
    )
    assert "super-secret" not in logged
    assert "print('private')" not in logged
    assert record.exc_info is None
