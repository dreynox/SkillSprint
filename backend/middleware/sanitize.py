import json
import nh3
import re
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message

# Sensitive or internal fields that should NOT be HTML-sanitized
# to avoid escaping special characters in passwords or tokens.
EXEMPT_FIELDS = {"password", "new_password", "token", "refresh_token"}

def sanitize_value(key, val):
    if isinstance(val, dict):
        return {k: sanitize_value(k, v) for k, v in val.items()}
    elif isinstance(val, list):
        return [sanitize_value(key, v) for v in val]
    elif isinstance(val, str):
        if key in EXEMPT_FIELDS:
            return val
        
        # Remove script elements and their contents
        val = re.sub(r'(?is)<script[^>]*>.*?</script>', '', val)
        # nh3.clean with tags=set() strips all HTML tags leaving just the text
        return nh3.clean(val, tags=set())
    
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
        content_type = headers.get(b"content-type", b"").decode("utf-8").lower()
        if not (content_type.startswith("application/json") or 
                (content_type.startswith("application/") and "+json" in content_type)):
            await self.app(scope, receive, send)
            return

        MAX_BODY_SIZE = 5 * 1024 * 1024  # 5MB limit
        
        chunks = []
        body_size = 0
        more_body = True
        while more_body:
            message = await receive()
            chunk = message.get("body", b"")
            body_size += len(chunk)
            if body_size > MAX_BODY_SIZE:
                async def send_413(send):
                    await send({
                        "type": "http.response.start",
                        "status": 413,
                        "headers": [(b"content-type", b"application/json")],
                    })
                    await send({
                        "type": "http.response.body",
                        "body": b'{"detail": "Request Entity Too Large"}',
                    })
                await send_413(send)
                return
            chunks.append(chunk)
            more_body = message.get("more_body", False)
            
        body = b"".join(chunks)

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
