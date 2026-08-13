import json
import bleach
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message

# Sensitive or internal fields that should NOT be HTML-sanitized
# to avoid escaping special characters in passwords or tokens.
EXEMPT_FIELDS = {"password", "new_password", "token", "refresh_token"}

def sanitize_value(key, val):
    if key in EXEMPT_FIELDS:
        return val

    if isinstance(val, str):
        # We allow a limited set of tags if needed, but for strict XSS
        # prevention on payloads that shouldn't have raw HTML, we strip it.
        # This prevents <script> or on-event attributes.
        return bleach.clean(val, strip=True)
    elif isinstance(val, dict):
        return {k: sanitize_value(k, v) for k, v in val.items()}
    elif isinstance(val, list):
        return [sanitize_value(key, v) for v in val]
    
    return val

class SanitizeMiddleware:
    """
    Middleware to intercept JSON requests and strip malicious HTML/XSS payloads.
    Uses bleach to sanitize all string fields in the request body, excluding passwords.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        if method not in ("POST", "PUT", "PATCH"):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        content_type = headers.get(b"content-type", b"").decode("utf-8")
        if not content_type.startswith("application/json"):
            await self.app(scope, receive, send)
            return

        # Read the body
        body = b""
        more_body = True
        while more_body:
            message = await receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)

        try:
            payload = json.loads(body)
            sanitized_payload = sanitize_value(None, payload)
            sanitized_bytes = json.dumps(sanitized_payload).encode("utf-8")
            
            # Update Content-Length
            headers[b"content-length"] = str(len(sanitized_bytes)).encode("utf-8")
            scope["headers"] = [(k, v) for k, v in headers.items()]

            async def new_receive():
                return {"type": "http.request", "body": sanitized_bytes, "more_body": False}
                
            await self.app(scope, new_receive, send)
        except json.JSONDecodeError:
            # Reconstruct original receive
            async def orig_receive():
                return {"type": "http.request", "body": body, "more_body": False}
            await self.app(scope, orig_receive, send)
