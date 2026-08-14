"""Request correlation IDs and request-scoped logging context."""

from __future__ import annotations

from contextvars import ContextVar
import logging
import re
import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send


REQUEST_ID_HEADER = "X-Request-ID"
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
_request_id: ContextVar[str | None] = ContextVar(
    "skillsprint_request_id",
    default=None,
)


def get_request_id() -> str | None:
    return _request_id.get()


def is_valid_request_id(value: str | None) -> bool:
    if value is None:
        return False
    return bool(_REQUEST_ID_PATTERN.fullmatch(value.strip()))


def resolve_request_id(value: str | None) -> str:
    if is_valid_request_id(value):
        return value.strip()
    return str(uuid.uuid4())


class RequestIdLogFilter(logging.Filter):
    """Attach the request ID to log records that pass through this filter."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not getattr(record, "request_id", None):
            record.request_id = get_request_id() or "-"
        return True


def install_request_id_log_filter() -> None:
    """Attach request ID support to root handlers already configured."""
    root = logging.getLogger()
    for handler in root.handlers:
        if not any(
            isinstance(item, RequestIdLogFilter)
            for item in handler.filters
        ):
            handler.addFilter(RequestIdLogFilter())


class RequestContextMiddleware:
    """Guarantee a correlation ID for normal HTTP responses."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        request_id = resolve_request_id(
            headers.get(REQUEST_ID_HEADER.lower())
        )
        scope.setdefault("state", {})["request_id"] = request_id
        token = _request_id.set(request_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers = list(message.get("headers", []))
                target = REQUEST_ID_HEADER.lower().encode("latin-1")
                response_headers = [
                    (key, value)
                    for key, value in response_headers
                    if key.lower() != target
                ]
                response_headers.append(
                    (
                        REQUEST_ID_HEADER.encode("latin-1"),
                        request_id.encode("latin-1"),
                    )
                )
                message["headers"] = response_headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            _request_id.reset(token)
