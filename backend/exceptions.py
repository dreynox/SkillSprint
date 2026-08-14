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
    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: ErrorCode.PAYLOAD_TOO_LARGE,
    status.HTTP_422_UNPROCESSABLE_ENTITY: ErrorCode.VALIDATION_ERROR,
    status.HTTP_429_TOO_MANY_REQUESTS: ErrorCode.RATE_LIMITED,
    status.HTTP_503_SERVICE_UNAVAILABLE: ErrorCode.SERVICE_UNAVAILABLE,
}


_PUBLIC_HTTP_MESSAGES = {
    status.HTTP_400_BAD_REQUEST: "Bad request",
    status.HTTP_401_UNAUTHORIZED: "Authentication required",
    status.HTTP_403_FORBIDDEN: "Forbidden",
    status.HTTP_404_NOT_FOUND: "Resource not found",
    status.HTTP_409_CONFLICT: "Conflict",
    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: "Payload too large",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "Request validation failed",
    status.HTTP_429_TOO_MANY_REQUESTS: "Too many requests",
    status.HTTP_503_SERVICE_UNAVAILABLE: "Service unavailable",
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


def _safe_route_template(request: Request) -> str:
    """Return a developer-defined route template, never the raw request path."""
    route = request.scope.get("route")
    template = getattr(route, "path", None)
    if isinstance(template, str) and template:
        return template
    return "<unmatched>"


def _safe_http_message(exc: HTTPException) -> str:
    """Map HTTP status to an application-owned public message.

    ``HTTPException.detail`` is deliberately ignored because existing routes may
    construct it from provider errors, user input, compiler source, or other
    sensitive values.
    """
    if exc.status_code >= 500:
        return "Internal server error"
    return _PUBLIC_HTTP_MESSAGES.get(exc.status_code, "Request failed")


def _validation_message(item: dict[str, Any]) -> str:
    """Normalize Pydantic errors to application-defined, input-free messages."""
    error_type = str(item.get("type", ""))
    context = item.get("ctx") or {}

    if error_type in {"missing", "value_error.missing"}:
        return "Field is required"

    if error_type in {
        "less_than_equal",
        "value_error.number.not_le",
    }:
        limit = context.get("le", context.get("limit_value"))
        if isinstance(limit, (int, float)):
            return f"Input should be less than or equal to {limit}"
        return "Input exceeds the maximum allowed value"

    if error_type in {
        "greater_than_equal",
        "value_error.number.not_ge",
    }:
        limit = context.get("ge", context.get("limit_value"))
        if isinstance(limit, (int, float)):
            return f"Input should be greater than or equal to {limit}"
        return "Input is below the minimum allowed value"

    if error_type in {"less_than", "value_error.number.not_lt"}:
        limit = context.get("lt", context.get("limit_value"))
        if isinstance(limit, (int, float)):
            return f"Input should be less than {limit}"
        return "Input exceeds the allowed value"

    if error_type in {"greater_than", "value_error.number.not_gt"}:
        limit = context.get("gt", context.get("limit_value"))
        if isinstance(limit, (int, float)):
            return f"Input should be greater than {limit}"
        return "Input is below the allowed value"

    if error_type in {
        "string_too_short",
        "value_error.any_str.min_length",
    }:
        minimum = context.get("min_length", context.get("limit_value"))
        if isinstance(minimum, int):
            return f"Text must contain at least {minimum} characters"
        return "Text is too short"

    if error_type in {
        "string_too_long",
        "value_error.any_str.max_length",
    }:
        maximum = context.get("max_length", context.get("limit_value"))
        if isinstance(maximum, int):
            return f"Text must contain at most {maximum} characters"
        return "Text is too long"

    if error_type in {
        "int_parsing",
        "type_error.integer",
    }:
        return "Input must be an integer"

    if error_type in {
        "float_parsing",
        "type_error.float",
    }:
        return "Input must be a number"

    if error_type in {
        "bool_parsing",
        "type_error.bool",
    }:
        return "Input must be a boolean"

    if error_type in {
        "enum",
        "type_error.enum",
    }:
        return "Input is not an allowed value"

    # Unknown/custom validator messages are not reflected because ``msg`` may
    # contain submitted passwords, tokens, compiler source, or other secrets.
    return "Invalid value"


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
                "message": _validation_message(item),
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
            "route": _safe_route_template(request),
            "error_count": len(exc.errors()),
        },
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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
            "route": _safe_route_template(request),
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

    logger.error(
        "Unhandled backend exception",
        extra={
            "request_id": request_id,
            "event": "unhandled_exception",
            "route": _safe_route_template(request),
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
