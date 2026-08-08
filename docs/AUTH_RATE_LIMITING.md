# Authentication Rate Limiting

SkillSprint protects authentication and password-reset endpoints with a
lightweight in-memory rate limiter. No Redis service is required for local
development.

## Protected endpoints

- `POST /auth/login`
- `POST /auth/register`
- `POST /auth/forgot-password/request-otp`
- `POST /auth/forgot-password/verify-otp`

## Default policy

| Operation | Default |
|---|---:|
| Failed login | 5 failures / 10 minutes |
| Registration | 10 requests / hour per requester |
| OTP request | 3 requests / 15 minutes per requester + normalized email |
| OTP verification | `OTP_MAX_ATTEMPTS` / 15 minutes per requester + normalized email |

All values are configurable through environment variables.

```env
AUTH_LOGIN_RATE_LIMIT=5
AUTH_LOGIN_RATE_WINDOW_SECONDS=600

AUTH_REGISTER_RATE_LIMIT=10
AUTH_REGISTER_RATE_WINDOW_SECONDS=3600

AUTH_OTP_REQUEST_RATE_LIMIT=3
AUTH_OTP_REQUEST_RATE_WINDOW_SECONDS=900

AUTH_OTP_VERIFY_RATE_LIMIT=5
AUTH_OTP_VERIFY_RATE_WINDOW_SECONDS=900
```

## Response behavior

When a bucket is blocked, the API returns:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 300
```

```json
{
  "detail": "Too many requests. Please try again later."
}
```

`Retry-After` is the remaining fixed-window duration in seconds.

## What increments a limit

Login attempts are recorded only after failed authentication. A successful
login resets the login-failure bucket.

Registration requests consume capacity because account creation is itself a
sensitive operation.

Password-reset OTP requests consume capacity whether or not the email exists.
This keeps observable behavior consistent and helps prevent account
enumeration.

Invalid OTP verification attempts consume both the rate-limit bucket and the
existing `PasswordResetOTP.attempts` counter.

When the database OTP attempt limit is reached, the OTP is marked consumed and
cannot be reused.

## Account enumeration protection

Password-reset request responses are intentionally identical for existing and
unknown email addresses:

```text
If an account exists for that email, a password-reset OTP has been sent.
```

OTP verification also uses one generic response for unknown accounts, missing
codes, expired codes, and invalid codes:

```text
Invalid or expired OTP
```

Raw email addresses are not stored in in-memory rate-limit keys. Keys contain a
SHA-256 digest of the requester and normalized identifier.

## Storage architecture

The initial implementation uses `InMemoryRateLimitStore`, suitable for a single
application process.

`RateLimiter` depends on the `RateLimitStore` protocol, so a later Redis-backed
store can implement the same methods:

```python
get(key)
set(key, count, window_started_at)
delete(key)
```

No endpoint changes are required when swapping the store.

## Testing

```powershell
cd backend
python -m pytest tests/test_auth_rate_limiting.py -v
```

The tests use an injectable fake clock and do not wait in real time.
