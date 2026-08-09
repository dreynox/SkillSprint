# Backend Error Responses and Request IDs

SkillSprint uses one error envelope across request validation errors,
authentication/authorization failures, `HTTPException` responses, and
unexpected backend exceptions.

## Request IDs

Every HTTP response includes:

```http
X-Request-ID: 7b530f9e-6c8e-4d84-9bf7-8e6df3e86731
```

Clients may provide an opaque request ID. Valid IDs are 8-128 characters,
begin with an alphanumeric character, and contain only letters, numbers,
`.`, `_`, `:`, or `-`. Missing or invalid values are replaced with a UUID.

The same ID is attached to backend error logs as `request_id`.

## Error envelope

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Resource not found",
    "request_id": "7b530f9e-...",
    "details": null
  }
}
```

HTTP status codes remain unchanged. Public error messages are application-owned
and are selected from the status code; arbitrary `HTTPException.detail` text is
not reflected to clients.

Authentication dependencies may emit either `401` or `403` for a missing bearer token depending on the installed FastAPI/Starlette version. The central handler intentionally preserves that framework status and maps it to the corresponding stable error code/message.

## Error codes and public messages

| HTTP status | Error code | Public message |
|---|---|---|
| 400 | `BAD_REQUEST` | `Bad request` |
| 401 | `AUTHENTICATION_REQUIRED` | `Authentication required` |
| 403 | `FORBIDDEN` | `Forbidden` |
| 404 | `RESOURCE_NOT_FOUND` | `Resource not found` |
| 409 | `CONFLICT` | `Conflict` |
| 413 | `PAYLOAD_TOO_LARGE` | `Payload too large` |
| 422 | `VALIDATION_ERROR` | `Request validation failed` |
| 429 | `RATE_LIMITED` | `Too many requests` |
| 503 | `SERVICE_UNAVAILABLE` | `Service unavailable` |
| other 5xx | `INTERNAL_ERROR` | `Internal server error` |

The implementation uses the Starlette 0.27-compatible constant names
`HTTP_413_REQUEST_ENTITY_TOO_LARGE` and `HTTP_422_UNPROCESSABLE_ENTITY`.

## Validation errors

Validation responses include safe field names and application-defined messages:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "request_id": "7b530f9e-...",
    "details": [
      {
        "field": "timeout",
        "message": "Input should be less than or equal to 30"
      }
    ]
  }
}
```

Pydantic's raw `msg` text and submitted input values are not returned. Known
validation types are normalized to stable application messages; unknown or
custom validator failures return `Invalid value`.

This prevents a custom validator message from echoing a password, token,
compiler source, or other submitted content.

## Internal errors

Unexpected exceptions return only:

```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Internal server error",
    "request_id": "7b530f9e-...",
    "details": null
  }
}
```

Server logs receive the exception type and safe stack locations containing only
file basename, line number, and function name. Exception messages and source
lines are not logged by the central handler.

## Sanitized route logging

Error logs use the developer-defined route template in a `route` field, for
example:

```text
/contests/{contest_id}
/secret/{secret_value}
```

They do **not** log `request.url.path`. Therefore an actual path parameter such
as a reset token, secret ID, or user-provided string is not copied into central
error logs. When no matched route template exists, the value is
`<unmatched>`.

## Structured log fields

Error handlers log safe metadata such as:

```text
request_id
event
route
method
status_code
error_code
exception_type
stack_trace
```

They do not log request bodies, raw request paths, Authorization headers,
cookies, compiler source code, passwords, tokens, or raw validation messages.

## Tests

```powershell
cd backend
python -m pytest tests/test_error_handling.py -v
```

The focused suite includes regression coverage for the Starlette 0.27 status
constants, sensitive `HTTPException.detail`, sensitive validator messages, and
route-template logging.
