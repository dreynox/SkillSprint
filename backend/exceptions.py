"""Consistent API error responses for SkillSprint."""

from __future__ import annotations

from enum import Enum
import logging
import os
import traceback
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status

from middleware.request_context import (
    REQUEST_ID_HEADER,
    get_request_id,
)


logger = logging.getLogger("skillsprint.errors")


class ErrorCode(str, Enum):
    BAD_REQUEST = "BAD_REQUEST"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    FORBIDDEN = "FORBIDDEN"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    CONFLICT = "CONFLICT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


_STATUS_CODE_MAP = {
    status.HTTP_400_BAD_REQUEST: ErrorCode.BAD_REQUEST,
    status.HTTP_401_UNAUTHORIZED: ErrorCode.AUTHENTICATION_REQUIRED,
    status.HTTP_403_FORBIDDEN: ErrorCode.FORBIDDEN,
    status.HTTP_404_NOT_FOUND: ErrorCode.RESOURCE_NOT_FOUND,
    status.HTTP_409_CONFLICT: ErrorCode.CONFLICT,
    status.HTTP_413_CONTENT_TOO_LARGE: ErrorCode.PAYLOAD_TOO_LARGE,
    status.HTTP_422_UNPROCESSABLE_CONTENT: ErrorCode.VALIDATION_ERROR,
    status.HTTP_429_TOO_MANY_REQUESTS: ErrorCode.RATE_LIMITED,
    status.HTTP_503_SERVICE_UNAVAILABLE: ErrorCode.SERVICE_UNAVAILABLE,
}


def error_code_for_status(status_code: int) -> ErrorCode:
    if status_code >= 500:
        if status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            return ErrorCode.SERVICE_UNAVAILABLE
        return ErrorCode.INTERNAL_ERROR
    return _STATUS_CODE_MAP.get(status_code, ErrorCode.BAD_REQUEST)


def _request_id(request: Request) -> str:
    return (
        getattr(request.state, "request_id", None)
        or get_request_id()
        or "-"
    )


def _headers(
    request_id: str,
    extra: dict[str, str] | None = None,
) -> dict[str, str]:
    headers = dict(extra or {})
    headers[REQUEST_ID_HEADER] = request_id
    return headers


def _envelope(
    *,
    code: ErrorCode,
    message: str,
    request_id: str,
    details: Any = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code.value,
            "message": message,
            "request_id": request_id,
            "details": details,
        }
    }


def _safe_http_message(exc: HTTPException) -> str:
    if exc.status_code >= 500:
        return "Internal server error"
    if isinstance(exc.detail, str) and exc.detail.strip():
        return exc.detail
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return "Authentication required"
    if exc.status_code == status.HTTP_403_FORBIDDEN:
        return "Forbidden"
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        return "Resource not found"
    return "Request failed"


def _validation_details(exc: RequestValidationError) -> list[dict[str, str]]:
    details: list[dict[str, str]] = []
    for item in exc.errors():
        location = [
            str(part)
            for part in item.get("loc", ())
            if part not in {"body", "query", "path", "header", "cookie"}
        ]
        details.append(
            {
                "field": ".".join(location) if location else "request",
                "message": str(item.get("msg", "Invalid value")),
            }
        )
    return details


def _safe_stack_trace(exc: Exception) -> list[dict[str, Any]]:
    """Return traceback locations without source lines or exception text."""
    frames = traceback.extract_tb(exc.__traceback__)
    return [
        {
            "file": os.path.basename(frame.filename),
            "line": frame.lineno,
            "function": frame.name,
        }
        for frame in frames
    ]


async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    request_id = _request_id(request)
    logger.info(
        "Request validation failed",
        extra={
            "request_id": request_id,
            "event": "request_validation_failed",
            "path": request.url.path,
            "error_count": len(exc.errors()),
        },
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        headers=_headers(request_id),
        content=_envelope(
            code=ErrorCode.VALIDATION_ERROR,
            message="Request validation failed",
            request_id=request_id,
            details=_validation_details(exc),
        ),
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    request_id = _request_id(request)
    code = error_code_for_status(exc.status_code)

    log_method = logger.error if exc.status_code >= 500 else logger.info
    log_method(
        "API HTTP exception",
        extra={
            "request_id": request_id,
            "event": "http_exception",
            "path": request.url.path,
            "status_code": exc.status_code,
            "error_code": code.value,
        },
    )

    safe_headers = {
        key: value
        for key, value in dict(exc.headers or {}).items()
        if key.lower() not in {"authorization", "cookie", "set-cookie"}
    }
    return JSONResponse(
        status_code=exc.status_code,
        headers=_headers(request_id, safe_headers),
        content=_envelope(
            code=code,
            message=_safe_http_message(exc),
            request_id=request_id,
            details=None,
        ),
    )


async def unexpected_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    request_id = _request_id(request)

    # Keep stack locations server-side, but do not log exception text, request
    # bodies, source-code lines, credentials, tokens, or Authorization headers.
    logger.error(
        "Unhandled backend exception",
        extra={
            "request_id": request_id,
            "event": "unhandled_exception",
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
            "stack_trace": _safe_stack_trace(exc),
        },
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        headers=_headers(request_id),
        content=_envelope(
            code=ErrorCode.INTERNAL_ERROR,
            message="Internal server error",
            request_id=request_id,
            details=None,
        ),
    )


def install_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        RequestValidationError,
        request_validation_exception_handler,
    )
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unexpected_exception_handler)
