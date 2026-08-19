import json
import nh3

def sanitize_data(data):
    """
    Recursively sanitize strings in the data payload.
    """
    if isinstance(data, str):
        # clean() defaults are quite strict and strip all dangerous tags (script, object, etc)
        # and dangerous attributes (onclick, javascript: URIs)
        return nh3.clean(data)
    elif isinstance(data, dict):
        return {k: sanitize_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_data(v) for v in data]
    return data

class SanitizeASGIMiddleware:
    """
    ASGI middleware to intercept JSON requests and sanitize them against XSS.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
            
        method = scope.get("method")
        if method not in ("POST", "PUT", "PATCH"):
            return await self.app(scope, receive, send)
            
        headers = dict(scope.get("headers", []))
        content_type = headers.get(b"content-type", b"").decode("utf-8")
        
        if "application/json" not in content_type:
            return await self.app(scope, receive, send)

        # Read the entire body from the receive channel
        body = b""
        more_body = True
        while more_body:
            message = await receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)

        try:
            payload = json.loads(body)
            sanitized_payload = sanitize_data(payload)
            sanitized_body = json.dumps(sanitized_payload).encode("utf-8")
            
            # Update the content-length header since body length might have changed
            new_headers = []
            for k, v in scope.get("headers", []):
                if k.lower() == b"content-length":
                    new_headers.append((b"content-length", str(len(sanitized_body)).encode("utf-8")))
                else:
                    new_headers.append((k, v))
            scope["headers"] = new_headers
            
        except Exception:
            # If JSON decoding fails, or any other issue, forward the original body
            sanitized_body = body

        # Create a new receive function that yields the modified body
        async def receive_sanitized():
            return {"type": "http.request", "body": sanitized_body, "more_body": False}

        await self.app(scope, receive_sanitized, send)
