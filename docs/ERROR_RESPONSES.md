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
    "message": "Contest not found",
    "request_id": "7b530f9e-...",
    "details": null
  }
}
```

HTTP status codes remain unchanged, so existing clients may continue using the
status while adopting the new body gradually.

## Error codes

| HTTP status | Error code |
|---|---|
| 400 | `BAD_REQUEST` |
| 401 | `AUTHENTICATION_REQUIRED` |
| 403 | `FORBIDDEN` |
| 404 | `RESOURCE_NOT_FOUND` |
| 409 | `CONFLICT` |
| 413 | `PAYLOAD_TOO_LARGE` |
| 422 | `VALIDATION_ERROR` |
| 429 | `RATE_LIMITED` |
| 503 | `SERVICE_UNAVAILABLE` |
| other 5xx | `INTERNAL_ERROR` |

## Validation errors

Validation responses contain field names and validator messages, but not the
submitted values:

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

Omitting raw input values protects passwords, access tokens, compiler source
code, and other request content.

## Unexpected exceptions

Clients receive only:

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

Server logs receive the exception type and a stack-location list containing
only file basename, line number, and function name. Exception messages and
source-code lines are not logged by this handler, preventing passwords, tokens,
submitted code, or other sensitive values embedded in exceptions from leaking
into logs.

Existing routes that raise an `HTTPException` with a 5xx status are also
generalized to `Internal server error` rather than returning `detail=str(exc)`.

## Structured log fields

Error handlers log safe metadata such as:

```text
request_id
event
path
method
status_code
error_code
exception_type
stack_trace
```

They do not log request bodies, Authorization headers, cookies, compiler source
code, passwords, or tokens.

## Tests

```powershell
cd backend
python -m pytest tests/test_error_handling.py -v
```
